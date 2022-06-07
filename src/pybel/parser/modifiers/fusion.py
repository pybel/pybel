# -*- coding: utf-8 -*-

"""Fusions.

Gene, RNA, miRNA, and protein  fusions are all represented with the same underlying data structure. Below
it is shown with uppercase letters referring to constants from :code:`pybel.constants` and. For example,
:code:`g(HGNC:BCR, fus(HGNC:JAK2, 1875, 2626))` is represented as:

.. code-block:: python

    from pybel.constants import *

    {
        FUNCTION: GENE,
        FUSION: {
            PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'BCR'},
            PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'JAK2'},
            RANGE_5P: {
                FUSION_REFERENCE: 'c',
                FUSION_START: '?',
                FUSION_STOP: 1875,
            },
            RANGE_3P: {
                FUSION_REFERENCE: 'c',
                FUSION_START: 2626,
                FUSION_STOP: '?',
            },
        },
    }


.. seealso::

    - BEL 2.0 specification on `fusions (2.6.1)
      <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_fusion_fus>`_
    - PyBEL module :py:class:`pybel.parser.modifiers.get_fusion_language`
    - PyBEL module :py:class:`pybel.parser.modifiers.get_legacy_fusion_language`
"""

from pyparsing import Group, Keyword, Optional, ParserElement, Suppress, oneOf
from pyparsing import pyparsing_common
from pyparsing import pyparsing_common as ppc
from pyparsing import replaceWith

from ..utils import WCW, nest
from ...constants import (
    CONCEPT,
    FUSION,
    FUSION_MISSING,
    FUSION_REFERENCE,
    FUSION_START,
    FUSION_STOP,
    PARTNER_3P,
    PARTNER_5P,
    RANGE_3P,
    RANGE_5P,
)

__all__ = [
    "fusion_tags",
    "get_fusion_language",
    "get_legacy_fusion_langauge",
]

fusion_tags = oneOf(["fus", "fusion"]).setParseAction(replaceWith(FUSION))
reference_seq = oneOf(["r", "p", "c"])
coordinate = pyparsing_common.integer | "?"
missing = Keyword("?")
range_coordinate_unquoted = missing(FUSION_MISSING) | (
    reference_seq(FUSION_REFERENCE) + Suppress(".") + coordinate(FUSION_START) + Suppress("_") + coordinate(FUSION_STOP)
)


def get_fusion_language(concept: ParserElement, permissive: bool = True) -> ParserElement:
    """Build a fusion parser."""
    range_coordinate = Suppress('"') + range_coordinate_unquoted + Suppress('"')

    if permissive:  # permissive to wrong quoting
        range_coordinate = range_coordinate | range_coordinate_unquoted

    return fusion_tags + nest(
        Group(Group(concept)(CONCEPT))(PARTNER_5P),
        Group(range_coordinate)(RANGE_5P),
        Group(Group(concept)(CONCEPT))(PARTNER_3P),
        Group(range_coordinate)(RANGE_3P),
    )


def get_legacy_fusion_langauge(concept: ParserElement, reference: str) -> ParserElement:
    """Build a legacy fusion parser."""
    break_start = (ppc.integer | "?").setParseAction(_fusion_break_handler_wrapper(reference, start=True))
    break_end = (ppc.integer | "?").setParseAction(_fusion_break_handler_wrapper(reference, start=False))

    res = (
        Group(concept(CONCEPT))(PARTNER_5P)
        + WCW
        + fusion_tags
        + nest(
            Group(concept(CONCEPT))(PARTNER_3P)
            + Optional(WCW + Group(break_start)(RANGE_5P) + WCW + Group(break_end)(RANGE_3P)),
        )
    )

    res.setParseAction(_fusion_legacy_handler)
    return res


def _fusion_legacy_handler(_, __, tokens):
    """Handle a legacy fusion."""
    if RANGE_5P not in tokens:
        tokens[RANGE_5P] = {FUSION_MISSING: "?"}
    if RANGE_3P not in tokens:
        tokens[RANGE_3P] = {FUSION_MISSING: "?"}
    return tokens


def _fusion_break_handler_wrapper(reference: str, start: bool):
    def fusion_break_handler(_, __, tokens):
        if tokens[0] == "?":
            tokens[FUSION_MISSING] = "?"
            return tokens
        else:  # The break point is specified as an integer
            tokens[FUSION_REFERENCE] = reference
            tokens[FUSION_START if start else FUSION_STOP] = "?"
            tokens[FUSION_STOP if start else FUSION_START] = int(tokens[0])
            return tokens

    return fusion_break_handler
