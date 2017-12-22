# -*- coding: utf-8 -*-

"""
Fusions
~~~~~~~

Gene, RNA, protein, and miRNA fusions are all represented with the same underlying data structure. Below
it is shown with uppercase letters referring to constants from :code:`pybel.constants` and. For example,
:code:`g(HGNC:BCR, fus(HGNC:JAK2, 1875, 2626))` is represented as:

.. code::

    {
        FUNCTION: GENE,
        FUSION: {
            PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'BCR'},
            PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'JAK2'},
            RANGE_5P: {
                FUSION_REFERENCE: 'c',
                FUSION_START: '?',
                FUSION_STOP: 1875

            },
            RANGE_3P: {
                FUSION_REFERENCE: 'c',
                FUSION_START: 2626,
                FUSION_STOP: '?'
            }
        }
    }


.. seealso::

    - BEL 2.0 specification on `fusions (2.6.1) <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_fusion_fus>`_
    - PyBEL module :py:class:`pybel.parser.modifiers.FusionParser`
"""

from pyparsing import Group, Keyword, Optional, Suppress, oneOf, pyparsing_common, pyparsing_common as ppc, replaceWith

from ..baseparser import BaseParser
from ..parse_identifier import IdentifierParser
from ..utils import WCW, nest
from ...constants import (
    FUSION, FUSION_MISSING, FUSION_REFERENCE, FUSION_START, FUSION_STOP, PARTNER_3P, PARTNER_5P,
    RANGE_3P, RANGE_5P,
)

__all__ = [
    'fusion_tags',
    'FusionParser'
]

fusion_tags = oneOf(['fus', 'fusion']).setParseAction(replaceWith(FUSION))


class FusionParser(BaseParser):
    """Parses the BEL representation of gene and gene product fusions"""

    def __init__(self, identifier_parser=None):
        """
        :param IdentifierParser identifier_parser: An identifier parser for checking the 3P and 5P partners
        """
        self.identifier_parser = identifier_parser if identifier_parser is not None else IdentifierParser()
        identifier = self.identifier_parser.language

        reference_seq = oneOf(['r', 'p', 'c'])
        coordinate = pyparsing_common.integer | '?'
        missing = Keyword('?')

        range_coordinate = missing(FUSION_MISSING) | (
            reference_seq(FUSION_REFERENCE) + Suppress('.') + coordinate(FUSION_START) + Suppress('_') + coordinate(
                FUSION_STOP))

        self.language = fusion_tags + nest(Group(identifier)(PARTNER_5P), Group(range_coordinate)(RANGE_5P),
                                           Group(identifier)(PARTNER_3P), Group(range_coordinate)(RANGE_3P))

        super(FusionParser, self).__init__(self.language)


def build_legacy_fusion(identifier, reference):
    break_start = (ppc.integer | '?').setParseAction(fusion_break_handler_wrapper(reference, start=True))
    break_end = (ppc.integer | '?').setParseAction(fusion_break_handler_wrapper(reference, start=False))

    res = identifier(PARTNER_5P) + WCW + fusion_tags + nest(identifier(PARTNER_3P) + Optional(
        WCW + Group(break_start)(RANGE_5P) + WCW + Group(break_end)(RANGE_3P)))

    res.setParseAction(fusion_legacy_handler)

    return res


def fusion_legacy_handler(line, position, tokens):
    if RANGE_5P not in tokens:
        tokens[RANGE_5P] = {FUSION_MISSING: '?'}
    if RANGE_3P not in tokens:
        tokens[RANGE_3P] = {FUSION_MISSING: '?'}
    return tokens


def fusion_break_handler_wrapper(reference, start):
    def fusion_break_handler(line, position, tokens):
        if tokens[0] == '?':
            tokens[FUSION_MISSING] = '?'
            return tokens
        else:  # The break point is specified as an integer
            tokens[FUSION_REFERENCE] = reference
            tokens[FUSION_START if start else FUSION_STOP] = '?'
            tokens[FUSION_STOP if start else FUSION_START] = int(tokens[0])
            return tokens

    return fusion_break_handler
