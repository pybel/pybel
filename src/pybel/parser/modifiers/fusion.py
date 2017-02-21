# -*- coding: utf-8 -*-

"""
Fusions
~~~~~~~

Gene, RNA, protein, and miRNA fusions are all represented with the same underlying data structure. Below
it is shown with uppercase letters referring to constants from :code:`pybel.constants` and
:class:`pybel.parser.FusionParser`. For example, :code:`g(HGNC:BCR, fus(HGNC:JAK2, 1875, 2626))` is represented as:

.. code::

    {
        FUNCTION: GENE,
        FUSION: {
            PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'BCR'},
            PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'JAK2'},
            RANGE_5P: {
                FusionParser.REFERENCE: 'c',
                FusionParser.START: '?',
                FusionParser.STOP: 1875

            },
            RANGE_3P: {
                FusionParser.REFERENCE: 'c',
                FusionParser.START: 2626,
                FusionParser.STOP: '?'
            }
        }
    }


.. seealso::

    BEL 2.0 specification on `fusions (2.6.1) <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_fusion_fus>`_
"""

from pyparsing import oneOf, replaceWith, pyparsing_common, Keyword, Suppress, Group, Optional
from pyparsing import pyparsing_common as ppc

from ..baseparser import BaseParser, nest, WCW
from ..parse_identifier import IdentifierParser
from ...constants import FUSION, PARTNER_5P, RANGE_5P, PARTNER_3P, RANGE_3P

fusion_tags = oneOf(['fus', 'fusion']).setParseAction(replaceWith(FUSION))


class FusionParser(BaseParser):
    REFERENCE = 'reference'
    START = 'left'
    STOP = 'right'
    MISSING = 'missing'

    def __init__(self, namespace_parser=None):
        self.identifier_parser = IdentifierParser() if namespace_parser is None else namespace_parser
        identifier = self.identifier_parser.language

        reference_seq = oneOf(['r', 'p', 'c'])
        coordinate = pyparsing_common.integer | '?'
        missing = Keyword('?')

        range_coordinate = missing(self.MISSING) | (
            reference_seq(self.REFERENCE) + Suppress('.') + coordinate(self.START) + Suppress('_') + coordinate(
                self.STOP))

        self.language = fusion_tags + nest(Group(identifier)(PARTNER_5P), Group(range_coordinate)(RANGE_5P),
                                           Group(identifier)(PARTNER_3P), Group(range_coordinate)(RANGE_3P))

        BaseParser.__init__(self, self.language)


def build_legacy_fusion(identifier, reference):
    break_start = (ppc.integer | '?').setParseAction(fusion_break_handler_wrapper(reference, start=True))
    break_end = (ppc.integer | '?').setParseAction(fusion_break_handler_wrapper(reference, start=False))

    res = identifier(PARTNER_5P) + WCW + fusion_tags + nest(identifier(PARTNER_3P) + Optional(
        WCW + Group(break_start)(RANGE_5P) + WCW + Group(break_end)(RANGE_3P)))

    res.setParseAction(fusion_legacy_handler)

    return res


def fusion_legacy_handler(s, l, tokens):
    if RANGE_5P not in tokens:
        tokens[RANGE_5P] = {FusionParser.MISSING: '?'}
    if RANGE_3P not in tokens:
        tokens[RANGE_3P] = {FusionParser.MISSING: '?'}
    return tokens


def fusion_break_handler_wrapper(reference, start):
    def fusion_break_handler(s, l, tokens):
        if tokens[0] == '?':
            tokens[FusionParser.MISSING] = '?'
            return tokens
        else:  # The break point is specified as an integer
            tokens[FusionParser.REFERENCE] = reference
            tokens[FusionParser.START if start else FusionParser.STOP] = '?'
            tokens[FusionParser.STOP if start else FusionParser.START] = int(tokens[0])
            return tokens

    return fusion_break_handler
