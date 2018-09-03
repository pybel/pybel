# -*- coding: utf-8 -*-

"""This module helps handle node data dictionaries."""

from .constants import (
    FRAGMENT, FRAGMENT_DESCRIPTION, FRAGMENT_START, FRAGMENT_STOP, FUNCTION,
    FUSION, FUSION_MISSING, FUSION_REFERENCE,
    FUSION_START, FUSION_STOP, GMOD, HGVS, IDENTIFIER, KIND, MEMBERS, MODIFIER, NAME, NAMESPACE,
    PARTNER_3P, PARTNER_5P, PMOD, PMOD_CODE, PMOD_POSITION, PRODUCTS, RANGE_3P, RANGE_5P, REACTANTS,
    REACTION, TARGET, VARIANTS,
)
from .dsl import (
    BaseAbundance, BaseEntity, CentralDogma, FUNC_TO_DSL, FUNC_TO_FUSION_DSL, FUNC_TO_LIST_DSL, FusionBase, Variant,
    fragment, fusion_range, gmod, hgvs, missing_fusion_range, pmod, reaction,
)

__all__ = [
    'parse_result_to_dsl',
]


def parse_result_to_dsl(tokens):
    """Convert a ParseResult to a PyBEL DSL object.

    :type tokens: dict or pyparsing.ParseResults
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
        return _fusion_to_dsl(tokens)

    return _simple_po_to_dict(tokens)


def _fusion_to_dsl(tokens):
    """Convert a PyParsing data dictionary to a PyBEL fusion data dictionary.

    :param tokens: A PyParsing data dictionary representing a fusion
    :type tokens: ParseResult
    :rtype: FusionBase
    """
    func = tokens[FUNCTION]
    fusion_dsl = FUNC_TO_FUSION_DSL[func]
    member_dsl = FUNC_TO_DSL[func]

    partner_5p = member_dsl(
        namespace=tokens[FUSION][PARTNER_5P][NAMESPACE],
        name=tokens[FUSION][PARTNER_5P][NAME]
    )

    partner_3p = member_dsl(
        namespace=tokens[FUSION][PARTNER_3P][NAMESPACE],
        name=tokens[FUSION][PARTNER_3P][NAME]
    )

    range_5p = _fusion_range_to_dsl(tokens[FUSION][RANGE_5P])
    range_3p = _fusion_range_to_dsl(tokens[FUSION][RANGE_3P])

    return fusion_dsl(
        partner_5p=partner_5p,
        partner_3p=partner_3p,
        range_5p=range_5p,
        range_3p=range_3p,
    )


def _fusion_range_to_dsl(tokens):
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


def _simple_po_to_dict(tokens):
    """Convert a simple named entity to a DSL object.

    :type tokens: ParseResult
    :rtype: BaseAbundance
    """
    dsl = FUNC_TO_DSL.get(tokens[FUNCTION])
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
    dsl = FUNC_TO_DSL.get(tokens[FUNCTION])
    if dsl is None:
        raise ValueError('invalid tokens: {}'.format(tokens))

    return dsl(
        namespace=tokens[NAMESPACE],
        name=tokens[NAME],
        variants=[
            _variant_to_dsl_helper(variant_tokens)
            for variant_tokens in tokens[VARIANTS]
        ],
    )


def _variant_to_dsl_helper(tokens):
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


def _list_po_to_dict(tokens):
    """
    :param tokens: PyParsing ParseObject
    :rtype: dict
    """
    func = tokens[FUNCTION]
    dsl = FUNC_TO_LIST_DSL[func]

    members = [parse_result_to_dsl(token) for token in tokens[MEMBERS]]

    return dsl(members)
