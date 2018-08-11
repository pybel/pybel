# -*- coding: utf-8 -*-

"""This module helps handle node data dictionaries."""

from .constants import (
    ABUNDANCE, ACTIVITY, BIOPROCESS, CELL_SECRETION, CELL_SURFACE_EXPRESSION, COMPLEX, COMPOSITE, DEGRADATION, EFFECT,
    FRAGMENT, FRAGMENT_DESCRIPTION, FRAGMENT_MISSING, FRAGMENT_START, FRAGMENT_STOP, FUNCTION, FUSION, FUSION_MISSING,
    FUSION_REFERENCE, FUSION_START, FUSION_STOP, GENE, GMOD, GMOD_ORDER, HGVS, IDENTIFIER, KIND, LOCATION, MEMBERS,
    MIRNA, MODIFIER, NAME, NAMESPACE, PARTNER_3P, PARTNER_5P, PATHOLOGY, PMOD, PMOD_CODE, PMOD_ORDER, PMOD_POSITION,
    PRODUCTS, PROTEIN, RANGE_3P, RANGE_5P, REACTANTS, REACTION, RNA, TARGET, TRANSLOCATION, VARIANTS,
)
from .dsl import cell_surface_expression, fusion_range, missing_fusion_range, secretion
from .dsl.nodes import (
    BaseAbundance, BaseEntity, CentralDogma, FusionBase, Variant, abundance, bioprocess, complex_abundance,
    composite_abundance, fragment, gene, gene_fusion, gmod, hgvs, mirna, named_complex_abundance, pathology, pmod,
    protein, protein_fusion, reaction, rna, rna_fusion,
)
from .exceptions import PyBELCanonicalizeError
from .utils import hash_node

__all__ = [
    'node_to_tuple',
    'hash_node_dict',
    'parse_result_to_dsl',
    'modifier_po_to_dict',
]

_list_func_to_dsl = {
    COMPLEX: complex_abundance,
    COMPOSITE: composite_abundance
}

_fusion_func_to_dsl = {
    GENE: gene_fusion,
    RNA: rna_fusion,
    PROTEIN: protein_fusion,
}

_func_dsl = {
    PROTEIN: protein,
    RNA: rna,
    MIRNA: mirna,
    GENE: gene,
    PATHOLOGY: pathology,
    BIOPROCESS: bioprocess,
    COMPLEX: named_complex_abundance,
    ABUNDANCE: abundance,
}


def hash_node_dict(node_dict):
    """Hash a PyBEL node data dictionary.

    :param dict node_dict:
    :rtype: str
    """
    return hash_node(node_to_tuple(node_dict))


def node_to_tuple(tokens):
    """Create a PyBEL node tuple given tokens from either PyParsing or following the PyBEL node data dictionary model.

    :param tokens: Either a PyParsing ParseObject or a PyBEL node data dictionary
    :type tokens: ParseObject or dict or BaseEntity
    :rtype: tuple
    """
    if isinstance(tokens, BaseEntity):
        return tokens.as_tuple()

    # raise ValueError('NO')

    if MODIFIER in tokens:
        return node_to_tuple(tokens[TARGET])

    elif REACTION == tokens[FUNCTION]:
        return _reaction_po_to_tuple(tokens)

    elif VARIANTS in tokens:
        return _variant_node_po_to_tuple(tokens)

    elif MEMBERS in tokens:
        return _list_po_to_tuple(tokens)

    elif FUSION in tokens:
        return _fusion_po_to_tuple(tokens)

    return _simple_to_tuple(tokens)


def _safe_get_dict(tokens):
    if hasattr(tokens, 'asDict'):
        return tokens.asDict()
    return dict(tokens)


def _identifier_to_tuple(tokens):
    """Extract the namespace and name pair from the tokens and creates a 2-tuple.

    :param dict tokens: A dictionary or slicable
    :type tokens: ParseResult or dict
    :rtype: tuple
    """
    return tokens[NAMESPACE], tokens[NAME]


def _fusion_range_po_to_dict(tokens):
    """Convert a PyParsing data dictionary into a PyBEL.

    :type tokens: ParseResult
    :rtype: pybel.dsl.FusionRangeBase
    """
    if FUSION_MISSING in tokens:
        return missing_fusion_range()

    return fusion_range(
        reference=tokens[FUSION_REFERENCE],
        start=tokens[FUSION_START],
        stop=tokens[FUSION_STOP]
    )


def _fusion_po_to_dict(tokens):
    """Convert a PyParsing data dictionary to a PyBEL fusion data dictionary.

    :param tokens: A PyParsing data dictionary representing a fusion
    :type tokens: ParseResult
    :rtype: FusionBase
    """
    func = tokens[FUNCTION]
    fusion_dsl = _fusion_func_to_dsl[func]
    member_dsl = _func_dsl[func]

    partner_5p = member_dsl(
        namespace=tokens[FUSION][PARTNER_5P][NAMESPACE],
        name=tokens[FUSION][PARTNER_5P][NAME]
    )

    partner_3p = member_dsl(
        namespace=tokens[FUSION][PARTNER_3P][NAMESPACE],
        name=tokens[FUSION][PARTNER_3P][NAME]
    )

    range_5p = _fusion_range_po_to_dict(tokens[FUSION][RANGE_5P])
    range_3p = _fusion_range_po_to_dict(tokens[FUSION][RANGE_3P])

    return fusion_dsl(
        partner_5p=partner_5p,
        partner_3p=partner_3p,
        range_5p=range_5p,
        range_3p=range_3p,
    )


def _simple_po_to_dict(tokens):
    """Convert a simple named entity to a DSL object.

    :type tokens: ParseResult
    :rtype: BaseAbundance
    """
    dsl = _func_dsl.get(tokens[FUNCTION])
    if dsl is None:
        raise ValueError('invalid tokens: {}'.format(tokens))

    return dsl(
        namespace=tokens[NAMESPACE],
        name=tokens[NAME],
    )


def _variant_po_to_dict(tokens):
    """Convert a PyParsing data dictionary to a central dogma abundance (i.e., Protein, RNA, miRNA, Gene).

    :type tokens: ParseResult
    :rtype: CentralDogma
    """
    dsl = _func_dsl.get(tokens[FUNCTION])
    if dsl is None:
        raise ValueError('invalid tokens: {}'.format(tokens))

    return dsl(
        namespace=tokens[NAMESPACE],
        name=tokens[NAME],
        variants=[
            _variant_tokens_to_dsl(variant_tokens)
            for variant_tokens in tokens[VARIANTS]
        ],
    )


def _variant_tokens_to_dsl(tokens):
    """Convert variant tokens to DSL objects.

    :type tokens: ParseResult
    :rtype: Variant
    """
    kind = tokens[KIND]

    if kind == HGVS:
        return hgvs(tokens[IDENTIFIER])

    if kind == GMOD:
        return gmod(
            name=tokens[IDENTIFIER][NAME],
            namespace=tokens[IDENTIFIER][NAMESPACE],
        )

    if kind == PMOD:
        return pmod(
            name=tokens[IDENTIFIER][NAME],
            namespace=tokens[IDENTIFIER][NAMESPACE],
            code=tokens.get(PMOD_CODE),
            position=tokens.get(PMOD_POSITION),
        )

    if kind == FRAGMENT:
        start, stop = tokens.get(FRAGMENT_START), tokens.get(FRAGMENT_STOP)
        return fragment(
            start=start,
            stop=stop,
            description=tokens.get(FRAGMENT_DESCRIPTION)
        )

    raise ValueError('invalid fragment kind: {}'.format(kind))


def _fusion_range_po_to_tuple(tokens, tag):
    """Convert a fusion range PyParsing data dictionary to a PyBEL fusion range tuple.

    :type tokens: ParseResult
    :param str tag: either :data:`pybel.constants.RANGE_3P` or :data:`pybel.constants.RANGE_5P`
    :rtype: tuple
    """
    if tag not in {RANGE_3P, RANGE_5P}:
        raise ValueError

    if tag not in tokens or FUSION_MISSING in tokens[tag]:
        return '?',

    return (
        tokens[tag][FUSION_REFERENCE],
        tokens[tag][FUSION_START],
        tokens[tag][FUSION_STOP]
    )


def _fusion_po_to_tuple(tokens):
    """Convert a PyParsing data dictionary to PyBEL node tuple.

    :type tokens: ParseResult
    :rtype: tuple
    """
    func = tokens[FUNCTION]
    fusion = tokens[FUSION]

    partner5p = _identifier_to_tuple(fusion[PARTNER_5P])
    partner3p = _identifier_to_tuple(fusion[PARTNER_3P])
    range5p = _fusion_range_po_to_tuple(fusion, RANGE_5P)
    range3p = _fusion_range_po_to_tuple(fusion, RANGE_3P)

    return (
        func,
        partner5p,
        range5p,
        partner3p,
        range3p,
    )


def _reaction_part_po_to_tuple(tokens):
    """
    :type tokens: ParseResult
    :rtype: tuple
    """
    return tuple(sorted(
        node_to_tuple(member)
        for member in tokens
    ))


def _reaction_po_to_tuple(tokens):
    """Convert a PyParsing ParseObject to PyBEL node tuple.

    :type tokens: ParseResult
    :rtype: tuple
    """
    reactants = _reaction_part_po_to_tuple(tokens[REACTANTS])
    products = _reaction_part_po_to_tuple(tokens[PRODUCTS])
    return (tokens[FUNCTION],) + (reactants,) + (products,)


def _reaction_po_to_dict(tokens):
    """
    :type tokens: ParseResult
    :rtype: dict
    """
    return reaction(
        reactants=_reaction_part_po_to_dict(tokens[REACTANTS]),
        products=_reaction_part_po_to_dict(tokens[PRODUCTS]),
    )


def _reaction_part_po_to_dict(tokens):
    """Convert a PyParsing result to a reaction.

    :type tokens: ParseResult
    :rtype: list[BaseAbundance]
    """
    return [parse_result_to_dsl(token) for token in tokens]


def _simple_to_tuple(tokens):
    """Convert the tokens returned by PyParsing for a simple node to a PyBEL node tuple.

    :type tokens: ParseResult or dict
    :rtype: tuple
    """
    if NAME in tokens:
        return (
            tokens[FUNCTION],
            tokens[NAMESPACE],
            tokens[NAME]
        )

    if IDENTIFIER in tokens:
        return (
            tokens[FUNCTION],
            tokens[NAMESPACE],
            tokens[IDENTIFIER]
        )

    raise PyBELCanonicalizeError('missing name and identifier in node data dict: {}'.format(tokens))


def _hgvs_po_to_tuple(tokens):
    """
    :type tokens: ParseResult or dict
    :rtype: tuple
    """
    return tokens[KIND], tokens[IDENTIFIER]


def _pmod_po_to_tuple(tokens):
    """
    :type tokens: ParseResult
    :rtype: tuple
    """
    identifier = _identifier_to_tuple(tokens[IDENTIFIER])
    params = tuple(tokens[key] for key in PMOD_ORDER[2:] if key in tokens)
    return (PMOD,) + (identifier,) + params


def _gmod_po_to_tuple(tokens):
    """
    :type tokens: ParseResult
    :rtype: tuple
    """
    identifier = _identifier_to_tuple(tokens[IDENTIFIER])
    params = tuple(tokens[key] for key in GMOD_ORDER[2:] if key in tokens)
    return (GMOD,) + (identifier,) + params


def _fragment_po_to_tuple(tokens):
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


def _variant_po_to_tuple(tokens):
    """
    :type tokens: pyparsing.ParseResults
    :rtype: tuple
    """
    if tokens[KIND] == HGVS:
        return _hgvs_po_to_tuple(tokens)

    elif tokens[KIND] == PMOD:
        return _pmod_po_to_tuple(tokens)

    elif tokens[KIND] == GMOD:
        return _gmod_po_to_tuple(tokens)

    elif tokens[KIND] == FRAGMENT:
        return _fragment_po_to_tuple(tokens)

    raise ValueError('Invalid value for tokens[KIND]: {}'.format(tokens[KIND]))


def _canonicalize_variants_helper(tokens):
    """Looks at the tokens[VARIANTS] dictionary

    :type tokens: ParseResult
    :rtype: tuple
    """
    return tuple(sorted(
        _variant_po_to_tuple(_safe_get_dict(token))
        for token in tokens
    ))


def _variant_node_po_to_tuple(tokens):
    """Converts the tokens returned by PyParsing for a node with variants to a PyBEL node tuple

    :param dict tokens:
    :rtype: tuple
    """
    return _simple_to_tuple(tokens) + _canonicalize_variants_helper(tokens[VARIANTS])


def _list_po_to_tuple(tokens):
    """
    :param tokens: PyParsing ParseObject
    :rtype: tuple
    """
    list_entries = tuple(sorted(
        node_to_tuple(member)
        for member in tokens[MEMBERS]
    ))

    return (tokens[FUNCTION],) + list_entries


def _list_po_to_dict(tokens):
    """
    :param tokens: PyParsing ParseObject
    :rtype: dict
    """
    func = tokens[FUNCTION]
    dsl = _list_func_to_dsl[func]

    members = [parse_result_to_dsl(token) for token in tokens[MEMBERS]]

    return dsl(members)


def parse_result_to_dsl(tokens):
    """Convert a ParseResult to a PyBEL DSL object

    :type tokens: ParseResult
    :rtype: BaseEntity
    """
    if MODIFIER in tokens:
        return parse_result_to_dsl(tokens[TARGET])

    elif REACTION == tokens[FUNCTION]:
        return _reaction_po_to_dict(tokens)

    elif VARIANTS in tokens:
        return _variant_po_to_dict(tokens)

    elif MEMBERS in tokens:
        return _list_po_to_dict(tokens)

    elif FUSION in tokens:
        return _fusion_po_to_dict(tokens)

    return _simple_po_to_dict(tokens)


def modifier_po_to_dict(tokens):
    """Get location, activity, and/or transformation information as a dictionary.

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
        attrs.update(secretion())

    elif tokens[MODIFIER] == CELL_SURFACE_EXPRESSION:
        attrs.update(cell_surface_expression())

    else:
        raise ValueError('Invalid value for tokens[MODIFIER]: {}'.format(tokens[MODIFIER]))

    return attrs
