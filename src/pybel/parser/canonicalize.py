# -*- coding: utf-8 -*-

from ..constants import *
from ..utils import list2tuple

__all__ = [
    'node_to_tuple',
]


def safe_get_dict(tokens):
    if hasattr(tokens, 'asDict'):
        return tokens.asDict()
    return dict(tokens)


def safe_get_list(tokens):
    if hasattr(tokens, 'asList'):
        return tokens.asList()
    return list(tokens)


def identifier_to_tuple(tokens):
    """Extracts the namespace and name pair from the tokens and creates a 2-tuple

    :param dict tokens: A dictionary or slicable
    :rtype: tuple
    """
    return tokens[NAMESPACE], tokens[NAME]


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
    """Converts a PyParsing data dictionary to a PyBEL fusion data dictionary

    :param ParseObject tokens: A PyParsing data dictionary representing a fusion
    :rtype: dict
    """
    return {
        FUNCTION: tokens[FUNCTION],
        FUSION: {
            PARTNER_5P: {
                NAMESPACE: tokens[FUSION][PARTNER_5P][NAMESPACE],
                NAME: tokens[FUSION][PARTNER_5P][NAME]
            },
            RANGE_5P: canonicalize_fusion_range_to_dict(tokens[FUSION][RANGE_5P]),
            PARTNER_3P: {
                NAMESPACE: tokens[FUSION][PARTNER_3P][NAMESPACE],
                NAME: tokens[FUSION][PARTNER_3P][NAME]
            },
            RANGE_3P: canonicalize_fusion_range_to_dict(tokens[FUSION][RANGE_3P])
        }
    }


def variant_po_to_dict(tokens):
    """Converts a PyParsing data dictionary to a PyBEL variant data dictionary

    :param tokens:
    :rtype: dict
    """
    attr_data = canonicalize_simple_to_dict(tokens)
    attr_data[VARIANTS] = [
        variant.asDict()
        for variant in tokens[VARIANTS]
    ]
    return attr_data


def fusion_range_to_tuple(tokens, tag):
    """

    :param tokens:
    :param str tag: either :data:`pybel.constants.RANGE_3P` or :data:`pybel.constants.RANGE_5P`
    :rtype: tuple
    """
    if tag not in {RANGE_3P, RANGE_5P}:
        raise ValueError

    if tag not in tokens or FUSION_MISSING in tokens[tag]:
        return '?',

    fusion_range = tokens[tag]

    return (
        fusion_range[FUSION_REFERENCE],
        fusion_range[FUSION_START],
        fusion_range[FUSION_STOP]
    )


def canonicalize_fusion(tokens):
    """Converts a PyParsing data dictionary to PyBEL node tuple

    :param ParseObject tokens:
    :rtype: tuple
    """
    function = tokens[FUNCTION]
    fusion = tokens[FUSION]

    partner5p = identifier_to_tuple(fusion[PARTNER_5P])
    partner3p = identifier_to_tuple(fusion[PARTNER_3P])
    range5p = fusion_range_to_tuple(fusion, RANGE_5P)
    range3p = fusion_range_to_tuple(fusion, RANGE_3P)

    return (
        function,
        partner5p,
        range5p,
        partner3p,
        range3p,
    )


def reaction_part_to_tuple(tokens):
    """

    :param tokens:
    :rtype: tuple
    """
    l = tokens.asList()
    return tuple(sorted(list2tuple(l)))


def reaction_po_to_tuple(tokens):
    """Converts a PyParsing ParseObject to PyBEL node tuple

    :param ParseObject tokens:
    :rtype: tuple
    """
    reactants = reaction_part_to_tuple(tokens[REACTANTS])
    products = reaction_part_to_tuple(tokens[PRODUCTS])
    return (tokens[FUNCTION],) + (reactants,) + (products,)


def simple_po_to_tuple(tokens):
    return (
        tokens[FUNCTION],
        tokens[IDENTIFIER][NAMESPACE],
        tokens[IDENTIFIER][NAME]
    )


def simple_to_tuple(tokens):
    """Converts the tokens returned by PyParsing for a simple node to a PyBEL node tuple

    :param dict tokens:
    :rtype: tuple
    """
    if IDENTIFIER in tokens:  # Means we're using PyParsing format
        return simple_po_to_tuple(tokens)

    return (
        tokens[FUNCTION],
        tokens[NAMESPACE],
        tokens[NAME]
    )


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
    identifier = identifier_to_tuple(tokens[IDENTIFIER])
    params = tuple(tokens[key] for key in PMOD_ORDER[2:] if key in tokens)
    return (PMOD,) + (identifier,) + params


def canonicalize_gmod(tokens):
    """

    :param tokens:
    :rtype: tuple
    """
    identifier = identifier_to_tuple(tokens[IDENTIFIER])
    params = tuple(tokens[key] for key in GMOD_ORDER[2:] if key in tokens)
    return (GMOD,) + (identifier,) + params


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


def _canonicalize_variants_helper(tokens):
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
    return simple_to_tuple(tokens) + _canonicalize_variants_helper(tokens[VARIANTS])


def list_node_to_tuple(tokens):
    """

    :param tokens:
    :rtype: tuple
    """
    return (tokens[FUNCTION],) + tuple(sorted(node_to_tuple(member) for member in tokens[MEMBERS]))


def node_to_tuple(tokens):
    """Given tokens from either PyParsing, or following the PyBEL node data dictionary model, create a PyBEL
    node tuple.

    :param tokens: Either a PyParsing ParseObject or a PyBEL node data dictionary
    :type tokens: ParseObject or dict
    :rtype: tuple
    """
    if MODIFIER in tokens:
        return node_to_tuple(tokens[TARGET])

    elif REACTION == tokens[FUNCTION]:
        return reaction_po_to_tuple(tokens)

    elif VARIANTS in tokens:
        return canonicalize_variant_node(tokens)

    elif MEMBERS in tokens:
        return list_node_to_tuple(tokens)

    elif FUSION in tokens:
        return canonicalize_fusion(tokens)

    return simple_to_tuple(tokens)


def modifier_po_to_dict(tokens):
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


def tuple_to_data(node_tuple):
    raise NotImplementedError
