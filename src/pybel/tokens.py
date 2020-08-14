# -*- coding: utf-8 -*-

"""This module helps handle node data dictionaries."""

from typing import Any, List, Mapping, Union

from pyparsing import ParseResults

from .constants import (
    CONCEPT, FRAGMENT, FRAGMENT_DESCRIPTION, FRAGMENT_START, FRAGMENT_STOP, FUNCTION, FUSION, FUSION_MISSING,
    FUSION_REFERENCE, FUSION_START, FUSION_STOP, GMOD, HGVS, IDENTIFIER, KIND, MEMBERS, NAME, NAMESPACE, PARTNER_3P,
    PARTNER_5P, PMOD, PMOD_CODE, PMOD_POSITION, PRODUCTS, RANGE_3P, RANGE_5P, REACTANTS, REACTION, VARIANTS, XREFS,
)
from .dsl import (
    BaseAbundance, BaseEntity, CentralDogma, EnumeratedFusionRange, FUNC_TO_DSL, FUNC_TO_FUSION_DSL, FUNC_TO_LIST_DSL,
    Fragment, FusionBase, FusionRangeBase, GeneModification, Hgvs, ListAbundance, MissingFusionRange,
    ProteinModification, Reaction, Variant,
)

__all__ = [
    'parse_result_to_dsl',
]


def parse_result_to_dsl(tokens) -> BaseEntity:
    """Convert a ParseResult to a PyBEL DSL object.

    :type tokens: dict or pyparsing.ParseResults
    """
    # if MODIFIER in tokens:
    #     return parse_result_to_dsl(tokens[TARGET])
    if REACTION == tokens[FUNCTION]:
        return _reaction_po_to_dict(tokens)

    elif VARIANTS in tokens:
        return _variant_po_to_dict(tokens)

    elif MEMBERS in tokens:
        if CONCEPT in tokens:
            return _list_po_with_concept_to_dict(tokens)
        return _list_po_to_dict(tokens)

    elif FUSION in tokens:
        return _fusion_to_dsl(tokens)

    return _simple_po_to_dict(tokens)


def _fusion_to_dsl(tokens) -> FusionBase:
    """Convert a PyParsing data dictionary to a PyBEL fusion data dictionary.

    :param tokens: A PyParsing data dictionary representing a fusion
    :type tokens: ParseResult
    """
    func = tokens[FUNCTION]
    fusion_dsl = FUNC_TO_FUSION_DSL[func]
    member_dsl = FUNC_TO_DSL[func]

    partner_5p = tokens[FUSION][PARTNER_5P]
    partner_5p_concept = (
        partner_5p[CONCEPT]
        if CONCEPT in tokens[FUSION][PARTNER_5P] else
        partner_5p
    )
    partner_5p_node = member_dsl(
        namespace=partner_5p_concept[NAMESPACE],
        name=partner_5p_concept[NAME],
        identifier=partner_5p_concept.get(IDENTIFIER),
        xrefs=partner_5p.get(XREFS),
    )

    partner_3p = tokens[FUSION][PARTNER_3P]
    partner_3p_concept = (
        partner_3p[CONCEPT]
        if CONCEPT in tokens[FUSION][PARTNER_3P] else
        partner_3p
    )
    partner_3p_node = member_dsl(
        namespace=partner_3p_concept[NAMESPACE],
        name=partner_3p_concept[NAME],
        identifier=partner_3p_concept.get(IDENTIFIER),
        xrefs=partner_3p.get(XREFS),
    )

    range_5p = _fusion_range_to_dsl(tokens[FUSION][RANGE_5P])
    range_3p = _fusion_range_to_dsl(tokens[FUSION][RANGE_3P])

    return fusion_dsl(
        partner_5p=partner_5p_node,
        partner_3p=partner_3p_node,
        range_5p=range_5p,
        range_3p=range_3p,
    )


def _fusion_range_to_dsl(tokens) -> FusionRangeBase:
    """Convert a PyParsing data dictionary into a PyBEL.

    :type tokens: ParseResult
    """
    if FUSION_MISSING in tokens:
        return MissingFusionRange()

    return EnumeratedFusionRange(
        reference=tokens[FUSION_REFERENCE],
        start=tokens[FUSION_START],
        stop=tokens[FUSION_STOP],
    )


def _simple_po_to_dict(tokens) -> BaseAbundance:
    """Convert a simple named entity to a DSL object.

    :type tokens: ParseResult
    """
    dsl = FUNC_TO_DSL.get(tokens[FUNCTION])
    if dsl is None:
        raise ValueError('invalid tokens: {}'.format(tokens))

    concept = tokens[CONCEPT]
    return dsl(
        namespace=concept[NAMESPACE],
        name=concept.get(NAME),
        identifier=concept.get(IDENTIFIER),
        xrefs=tokens.get(XREFS),
    )


def _variant_po_to_dict(tokens) -> CentralDogma:
    """Convert a PyParsing data dictionary to a central dogma abundance (i.e., Protein, RNA, miRNA, Gene).

    :type tokens: ParseResult
    """
    dsl = FUNC_TO_DSL.get(tokens[FUNCTION])
    if dsl is None:
        raise ValueError('invalid tokens: {}'.format(tokens))

    concept = tokens[CONCEPT]
    return dsl(
        namespace=concept[NAMESPACE],
        name=concept[NAME],
        identifier=concept.get(IDENTIFIER),
        xrefs=tokens.get(XREFS),
        variants=[
            _variant_to_dsl_helper(variant_tokens)
            for variant_tokens in tokens[VARIANTS]
        ],
    )


def _variant_to_dsl_helper(tokens) -> Variant:
    """Convert variant tokens to DSL objects.

    :type tokens: ParseResult
    """
    kind = tokens[KIND]

    if kind == HGVS:
        return Hgvs(tokens[HGVS])

    if kind == GMOD:
        concept = tokens[CONCEPT]
        return GeneModification(
            name=concept[NAME],
            namespace=concept[NAMESPACE],
            identifier=concept.get(IDENTIFIER),
            xrefs=tokens.get(XREFS),
        )

    if kind == PMOD:
        concept = tokens[CONCEPT]
        return ProteinModification(
            name=concept[NAME],
            namespace=concept[NAMESPACE],
            identifier=concept.get(IDENTIFIER),
            xrefs=tokens.get(XREFS),
            code=tokens.get(PMOD_CODE),
            position=tokens.get(PMOD_POSITION),
        )

    if kind == FRAGMENT:
        start, stop = tokens.get(FRAGMENT_START), tokens.get(FRAGMENT_STOP)
        return Fragment(
            start=start,
            stop=stop,
            description=tokens.get(FRAGMENT_DESCRIPTION),
        )

    raise ValueError('invalid fragment kind: {}'.format(kind))


def _reaction_po_to_dict(tokens) -> Reaction:
    """Convert a reaction parse object to a DSL.

    :type tokens: ParseResult
    """
    return Reaction(
        reactants=_parse_tokens_list(tokens[REACTANTS]),
        products=_parse_tokens_list(tokens[PRODUCTS]),
    )


def _list_po_with_concept_to_dict(tokens: Union[ParseResults, Mapping[str, Any]]) -> ListAbundance:
    """Convert a list parse object to a node.

    :type tokens: ParseResult
    """
    func = tokens[FUNCTION]
    dsl = FUNC_TO_LIST_DSL[func]
    members = _parse_tokens_list(tokens[MEMBERS])

    concept = tokens[CONCEPT]
    return dsl(
        members=members,
        namespace=concept[NAMESPACE],
        name=concept.get(NAME),
        identifier=concept.get(IDENTIFIER),
        xrefs=tokens.get(XREFS),
    )


def _list_po_to_dict(tokens) -> ListAbundance:
    """Convert a list parse object to a node.

    :type tokens: ParseResult
    """
    func = tokens[FUNCTION]
    dsl = FUNC_TO_LIST_DSL[func]
    members = _parse_tokens_list(tokens[MEMBERS])
    return dsl(members)


def _parse_tokens_list(tokens) -> List[BaseEntity]:
    """Convert a PyParsing result to a reaction.

    :type tokens: ParseResult
    """
    return [
        parse_result_to_dsl(token)
        for token in tokens
    ]
