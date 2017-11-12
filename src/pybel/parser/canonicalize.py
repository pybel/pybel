# -*- coding: utf-8 -*-

from ..constants import *
from ..utils import hash_node

__all__ = [
    'node_to_tuple',
    'sort_dict_list',
    'sort_variant_dict_list'
]


def safe_get_dict(tokens):
    if hasattr(tokens, 'asDict'):
        return tokens.asDict()
    return dict(tokens)


def identifier_to_tuple(tokens):
    """Extracts the namespace and name pair from the tokens and creates a 2-tuple

    :param dict tokens: A dictionary or slicable
    :type tokens: ParseResult or dict
    :rtype: tuple
    """
    return tokens[NAMESPACE], tokens[NAME]


# TODO figure out how to just get dictionary rather than slicing it up like this
def fusion_range_po_to_dict(tokens):
    """
    :type tokens: ParseResult
    :rtype: dict
    """
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


def fusion_po_to_dict(tokens):
    """Converts a PyParsing data dictionary to a PyBEL fusion data dictionary

    :param tokens: A PyParsing data dictionary representing a fusion
    :type tokens: ParseResult
    :rtype: dict
    """
    return {
        FUNCTION: tokens[FUNCTION],
        FUSION: {
            PARTNER_5P: {
                NAMESPACE: tokens[FUSION][PARTNER_5P][NAMESPACE],
                NAME: tokens[FUSION][PARTNER_5P][NAME]
            },
            RANGE_5P: fusion_range_po_to_dict(tokens[FUSION][RANGE_5P]),
            PARTNER_3P: {
                NAMESPACE: tokens[FUSION][PARTNER_3P][NAMESPACE],
                NAME: tokens[FUSION][PARTNER_3P][NAME]
            },
            RANGE_3P: fusion_range_po_to_dict(tokens[FUSION][RANGE_3P])
        }
    }


def sort_variant_dict_list(variants):
    return sorted(variants, key=variant_po_to_tuple)


def variant_po_to_dict_helper(tokens):
    """Converts a PyParsing data dictionary to a PyBEL variant data dictionary

    :type tokens: ParseResult
    :rtype: dict
    """
    return [
        safe_get_dict(variant)
        for variant in sort_variant_dict_list(tokens[VARIANTS])
    ]


def variant_po_to_dict(tokens):
    """Converts a PyParsing data dictionary to a PyBEL variant data dictionary

    :type tokens: ParseResult
    :rtype: dict
    """
    attr_data = simple_po_to_dict(tokens)
    attr_data[VARIANTS] = variant_po_to_dict_helper(tokens)
    return attr_data


def fusion_range_po_to_tuple(tokens, tag):
    """
    :type tokens: ParseResult
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


def fusion_po_to_tuple(tokens):
    """Converts a PyParsing data dictionary to PyBEL node tuple

    :type tokens: ParseResult
    :rtype: tuple
    """
    function = tokens[FUNCTION]
    fusion = tokens[FUSION]

    partner5p = identifier_to_tuple(fusion[PARTNER_5P])
    partner3p = identifier_to_tuple(fusion[PARTNER_3P])
    range5p = fusion_range_po_to_tuple(fusion, RANGE_5P)
    range3p = fusion_range_po_to_tuple(fusion, RANGE_3P)

    return (
        function,
        partner5p,
        range5p,
        partner3p,
        range3p,
    )


def reaction_part_po_to_tuple(tokens):
    """
    :type tokens: ParseResult
    :rtype: tuple
    """
    return tuple(sorted(
        node_to_tuple(member)
        for member in tokens
    ))


def sort_dict_list(tokens):
    """Sorts a list of PyBEL data dictionaries to their canonical ordering"""
    return sorted(tokens, key=node_to_tuple)


def reaction_part_po_to_dict(tokens):
    """
    :type tokens: ParseResult
    :rtype: dict
    """
    return [
        po_to_dict(token)
        for token in sort_dict_list(tokens)
    ]


def reaction_po_to_tuple(tokens):
    """Converts a PyParsing ParseObject to PyBEL node tuple

    :type tokens: ParseResult
    :rtype: tuple
    """
    reactants = reaction_part_po_to_tuple(tokens[REACTANTS])
    products = reaction_part_po_to_tuple(tokens[PRODUCTS])
    return (tokens[FUNCTION],) + (reactants,) + (products,)


def reaction_po_to_dict(tokens):
    """
    :type tokens: ParseResult
    :rtype: dict
    """
    return {
        FUNCTION: REACTION,
        REACTANTS: reaction_part_po_to_dict(tokens[REACTANTS]),
        PRODUCTS: reaction_part_po_to_dict(tokens[PRODUCTS]),
    }


def simple_po_to_tuple(tokens):
    """
    :type tokens: ParseResult
    :rtype: tuple
    """
    return (
        tokens[FUNCTION],
        tokens[NAMESPACE],
        tokens[NAME]
    )


def simple_po_to_dict(tokens):
    """
    :type tokens: ParseResult
    :rtype: dict
    """
    return {
        FUNCTION: tokens[FUNCTION],
        NAMESPACE: tokens[NAMESPACE],
        NAME: tokens[NAME]
    }


def simple_to_tuple(tokens):
    """Converts the tokens returned by PyParsing for a simple node to a PyBEL node tuple

    :type tokens: ParseResult or dict
    :rtype: tuple
    """
    return (
        tokens[FUNCTION],
        tokens[NAMESPACE],
        tokens[NAME]
    )


def hgvs_po_to_tuple(tokens):
    """
    :type tokens: ParseResult or dict
    :rtype: tuple
    """
    return tokens[KIND], tokens[IDENTIFIER]


def pmod_po_to_tuple(tokens):
    """
    :type tokens: ParseResult
    :rtype: tuple
    """
    identifier = identifier_to_tuple(tokens[IDENTIFIER])
    params = tuple(tokens[key] for key in PMOD_ORDER[2:] if key in tokens)
    return (PMOD,) + (identifier,) + params


def gmod_po_to_tuple(tokens):
    """
    :type tokens: ParseResult
    :rtype: tuple
    """
    identifier = identifier_to_tuple(tokens[IDENTIFIER])
    params = tuple(tokens[key] for key in GMOD_ORDER[2:] if key in tokens)
    return (GMOD,) + (identifier,) + params


def fragment_po_to_tuple(tokens):
    """
    :type tokens: ParseResult
    :rtype: tuple
    """
    if FRAGMENT_MISSING in tokens:
        result = FRAGMENT, '?'
    else:
        result = FRAGMENT, (tokens[FRAGMENT_START], tokens[FRAGMENT_STOP])

    if FRAGMENT_DESCRIPTION in tokens:
        return result + (tokens[FRAGMENT_DESCRIPTION],)

    return result


def variant_po_to_tuple(tokens):
    """
    :type tokens: pyparsing.ParseResults
    :rtype: tuple
    """
    if tokens[KIND] == HGVS:
        return hgvs_po_to_tuple(tokens)

    elif tokens[KIND] == PMOD:
        return pmod_po_to_tuple(tokens)

    elif tokens[KIND] == GMOD:
        return gmod_po_to_tuple(tokens)

    elif tokens[KIND] == FRAGMENT:
        return fragment_po_to_tuple(tokens)

    raise ValueError('Invalid value for tokens[KIND]: {}'.format(tokens[KIND]))


def _canonicalize_variants_helper(tokens):
    """Looks at the tokens[VARIANTS] dictionary

    :type tokens: ParseResult
    :rtype: tuple
    """
    return tuple(sorted(
        variant_po_to_tuple(safe_get_dict(token))
        for token in tokens
    ))


def variant_node_po_to_tuple(tokens):
    """Converts the tokens returned by PyParsing for a node with variants to a PyBEL node tuple

    :param dict tokens:
    :rtype: tuple
    """
    return simple_to_tuple(tokens) + _canonicalize_variants_helper(tokens[VARIANTS])


def list_po_to_tuple(tokens):
    """
    :param tokens: PyParsing ParseObject
    :rtype: tuple
    """
    list_entries = tuple(sorted(
        node_to_tuple(member)
        for member in tokens[MEMBERS]
    ))

    return (tokens[FUNCTION],) + list_entries


def list_po_to_dict(tokens):
    """
    :param tokens: PyParsing ParseObject
    :rtype: dict
    """
    list_entries = [
        po_to_dict(token)
        for token in sort_dict_list(tokens[MEMBERS])
    ]

    return {
        FUNCTION: tokens[FUNCTION],
        MEMBERS: list_entries
    }


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
        return variant_node_po_to_tuple(tokens)

    elif MEMBERS in tokens:
        return list_po_to_tuple(tokens)

    elif FUSION in tokens:
        return fusion_po_to_tuple(tokens)

    return simple_to_tuple(tokens)


def hash_node_dict(node_dict):
    """Hashes a PyBEL node data dictionary

    :param dict node_dict:
    :rtype: str
    """
    return hash_node(node_to_tuple(node_dict))


def po_to_dict(tokens):
    """
    :type tokens: ParseResult
    :rtype: dict
    """
    if MODIFIER in tokens:
        return po_to_dict(tokens[TARGET])

    elif REACTION == tokens[FUNCTION]:
        return reaction_po_to_dict(tokens)

    elif VARIANTS in tokens:
        return variant_po_to_dict(tokens)

    elif MEMBERS in tokens:
        return list_po_to_dict(tokens)

    elif FUSION in tokens:
        return fusion_po_to_dict(tokens)

    return simple_po_to_dict(tokens)


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
