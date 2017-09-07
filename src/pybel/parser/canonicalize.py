# -*- coding: utf-8 -*-

from ..constants import *
from ..utils import list2tuple


def canonicalize_simple_to_dict(tokens):
    return {
        FUNCTION: tokens[FUNCTION],
        NAMESPACE: tokens[IDENTIFIER][NAMESPACE],
        NAME: tokens[IDENTIFIER][NAME]
    }


# TODO figure out how to just get dictionary rather than slicing it up like this
def canonicalize_fusion_range_to_dict(tokens):
    if FUSION_MISSING in tokens:
        return {
            FUSION_MISSING: '?'
        }
    else:
        return {
            FUSION_REFERENCE: tokens[FUSION_REFERENCE],
            FUSION_START: tokens[FUSION_START],
            FUSION_STOP: tokens[FUSION_STOP]
        }


def canonicalize_fusion_to_dict(tokens):
    f = tokens[FUSION]
    return {
        FUNCTION: tokens[FUNCTION],
        FUSION: {
            PARTNER_5P: {
                NAMESPACE: f[PARTNER_5P][NAMESPACE],
                NAME: f[PARTNER_5P][NAME]
            },
            RANGE_5P: canonicalize_fusion_range_to_dict(f[RANGE_5P]),
            PARTNER_3P: {
                NAMESPACE: f[PARTNER_3P][NAMESPACE],
                NAME: f[PARTNER_3P][NAME]
            },
            RANGE_3P: canonicalize_fusion_range_to_dict(f[RANGE_3P])
        }
    }


def canonicalize_variant_node_to_dict(tokens):
    attr_data = canonicalize_simple_to_dict(tokens)
    attr_data[VARIANTS] = [variant.asDict() for variant in tokens[VARIANTS]]
    return attr_data


def canonicalize_fusion_range(tokens, tag):
    if tag in tokens and FUSION_MISSING not in tokens[tag]:
        fusion_range = tokens[tag]
        return fusion_range[FUSION_REFERENCE], fusion_range[FUSION_START], fusion_range[FUSION_STOP]
    else:
        return '?',


def canonicalize_fusion(tokens):
    function = tokens[FUNCTION]
    fusion = tokens[FUSION]

    partner5p = fusion[PARTNER_5P]
    partner3p = fusion[PARTNER_3P]
    range5p = canonicalize_fusion_range(fusion, RANGE_5P)
    range3p = canonicalize_fusion_range(fusion, RANGE_3P)

    return function, (partner5p[NAMESPACE], partner5p[NAME]), range5p, (partner3p[NAMESPACE], partner3p[NAME]), range3p


def canonicalize_reaction(tokens):
    reactants = tuple(sorted(list2tuple(tokens[REACTANTS].asList())))
    products = tuple(sorted(list2tuple(tokens[PRODUCTS].asList())))
    return (tokens[FUNCTION],) + (reactants,) + (products,)


def canonicalize_simple(tokens):
    """Converts the tokens returned by PyParsing for a simple node to a PyBEL node tuple

    :param dict tokens:
    :rtype: tuple
    """
    if IDENTIFIER in tokens:  # Means we're using PyParsing format
        return tokens[FUNCTION], tokens[IDENTIFIER][NAMESPACE], tokens[IDENTIFIER][NAME]

    return tokens[FUNCTION], tokens[NAMESPACE], tokens[NAME]


def safe_get_dict(tokens):
    if hasattr(tokens, 'asDict'):
        return tokens.asDict()
    return dict(tokens)


def canonicalize_hgvs(tokens):
    """

    :param tokens:
    :rtype: tuple
    """
    return tokens[KIND], tokens[IDENTIFIER]


def canonicalize_pmod(tokens):
    """

    :param tokens:
    :rtype: tuple
    """
    return (PMOD, (tokens[IDENTIFIER][NAMESPACE], tokens[IDENTIFIER][NAME])) + tuple(
        tokens[key] for key in PMOD_ORDER[2:] if key in tokens)


def canonicalize_gmod(tokens):
    """

    :param tokens:
    :rtype: tuple
    """
    return (GMOD, (tokens[IDENTIFIER][NAMESPACE], tokens[IDENTIFIER][NAME])) + tuple(
        tokens[key] for key in GMOD_ORDER[2:] if key in tokens)


def canonicalize_frag(tokens):
    """

    :param tokens:
    :rtype: tuple
    """
    if FRAGMENT_MISSING in tokens:
        result = FRAGMENT, '?'
    else:
        result = FRAGMENT, (tokens[FRAGMENT_START], tokens[FRAGMENT_STOP])

    if FRAGMENT_DESCRIPTION in tokens:
        return result + (tokens[FRAGMENT_DESCRIPTION],)

    return result


def canonicalize_variant(tokens):
    """

    :param tokens:
    :rtype: tuple
    """
    if tokens[KIND] == HGVS:
        return canonicalize_hgvs(tokens)

    elif tokens[KIND] == PMOD:
        return canonicalize_pmod(tokens)

    elif tokens[KIND] == GMOD:
        return canonicalize_gmod(tokens)

    elif tokens[KIND] == FRAGMENT:
        return canonicalize_frag(tokens)

    raise ValueError('Invalid value for tokens[KIND]: {}'.format(tokens[KIND]))


def _canonicalize_variants_heper(tokens):
    """Looks at the tokens[VARIANTS] dictionary

    :param tokens:
    :rtype: tuple
    """
    return tuple(sorted(
        canonicalize_variant(safe_get_dict(token))
        for token in tokens
    ))


def canonicalize_variant_node(tokens):
    """Converts the tokens returned by PyParsing for a node with variants to a PyBEL node tuple

    :param dict tokens:
    :rtype: tuple
    """
    return canonicalize_simple(tokens) + _canonicalize_variants_heper(tokens[VARIANTS])


def canonicalize_list_node(tokens):
    return (tokens[FUNCTION],) + tuple(sorted(canonicalize_node(member) for member in tokens[MEMBERS]))


def canonicalize_node(tokens):
    """Given tokens, returns node name

    :param ParseObject or dict tokens:
    :rtype: tuple
    """
    if MODIFIER in tokens:
        return canonicalize_node(tokens[TARGET])

    elif REACTION == tokens[FUNCTION]:
        return canonicalize_reaction(tokens)

    elif VARIANTS in tokens:
        return canonicalize_variant_node(tokens)

    elif MEMBERS in tokens:
        return canonicalize_list_node(tokens)

    elif FUSION in tokens:
        return canonicalize_fusion(tokens)

    return canonicalize_simple(tokens)


def canonicalize_modifier(tokens):
    """Get activity, transformation, or transformation information as a dictionary

    :return: a dictionary describing the modifier
    :rtype: dict
    """
    attrs = {}

    if LOCATION in tokens:
        attrs[LOCATION] = tokens[LOCATION].asDict()

    if MODIFIER not in tokens:
        return attrs

    if LOCATION in tokens[TARGET]:
        attrs[LOCATION] = tokens[TARGET][LOCATION].asDict()

    if tokens[MODIFIER] == DEGRADATION:
        attrs[MODIFIER] = tokens[MODIFIER]

    elif tokens[MODIFIER] == ACTIVITY:
        attrs[MODIFIER] = tokens[MODIFIER]

        if EFFECT in tokens:
            attrs[EFFECT] = dict(tokens[EFFECT])

    elif tokens[MODIFIER] == TRANSLOCATION:
        attrs[MODIFIER] = tokens[MODIFIER]

        if EFFECT in tokens:
            attrs[EFFECT] = tokens[EFFECT].asDict()

    elif tokens[MODIFIER] == CELL_SECRETION:
        attrs[MODIFIER] = TRANSLOCATION
        attrs[EFFECT] = {
            FROM_LOC: {NAMESPACE: GOCC_KEYWORD, NAME: 'intracellular'},
            TO_LOC: {NAMESPACE: GOCC_KEYWORD, NAME: 'extracellular space'}
        }

    elif tokens[MODIFIER] == CELL_SURFACE_EXPRESSION:
        attrs[MODIFIER] = TRANSLOCATION
        attrs[EFFECT] = {
            FROM_LOC: {NAMESPACE: GOCC_KEYWORD, NAME: 'intracellular'},
            TO_LOC: {NAMESPACE: GOCC_KEYWORD, NAME: 'cell surface'}
        }

    else:
        raise ValueError('Invalid value for tokens[MODIFIER]: {}'.format(tokens[MODIFIER]))

    return attrs


def data_to_tuple(node_data):
    return canonicalize_node(node_data)


def tuple_to_data(node_tuple):
    raise NotImplementedError
