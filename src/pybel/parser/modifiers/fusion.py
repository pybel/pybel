# -*- coding: utf-8 -*-

"""
Fusions
~~~~~~~

Gene, RNA, protein, and miRNA fusions are all represented with the same underlying data structure. Below
it is shown with uppercase letters referring to entries in :code:`pybel.constants` and
:class:`pybel.parser.FusionParser`. For example, :code:`g(HGNC:BCR, fus(HGNC:JAK2, 1875, 2626))` is represented as:

.. code::

    {
        FUNCTION: GENE,
        FUSION: {
            PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'BCR'},
            PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'JAK2'},
            RANGE_5P: {
                FusionParser.REF: 'c',
                FusionParser.LEFT: '?',
                FusionParser.RIGHT: 1875

            },
            RANGE_3P: {
                FusionParser.REF: 'c',
                FusionParser.LEFT: 2626,
                FusionParser.RIGHT: '?'
            }
        }
    }


.. seealso:: 2.6.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_fusion_fus
"""

from pyparsing import oneOf, replaceWith, pyparsing_common, Keyword, Suppress, Group

from ..baseparser import BaseParser, nest
from ..parse_identifier import IdentifierParser
from ...constants import FUSION, PARTNER_5P, RANGE_5P, PARTNER_3P, RANGE_3P


class FusionParser(BaseParser):
    REF = 'reference'
    LEFT = 'left'
    RIGHT = 'right'
    MISSING = 'missing'
    fusion_tags = oneOf(['fus', 'fusion']).setParseAction(replaceWith(FUSION))

    def __init__(self, namespace_parser=None):
        self.identifier_parser = namespace_parser if namespace_parser is not None else IdentifierParser()
        identifier = self.identifier_parser.get_language()

        reference_seq = oneOf(['r', 'p', 'c'])
        coordinate = pyparsing_common.integer | '?'
        missing = Keyword('?')

        range_coordinate = missing(self.MISSING) | (
            reference_seq(self.REF) + Suppress('.') + coordinate(self.LEFT) + Suppress('_') + coordinate(self.RIGHT))

        self.language = self.fusion_tags + nest(Group(identifier)(PARTNER_5P), Group(range_coordinate)(RANGE_5P),
                                                Group(identifier)(PARTNER_3P), Group(range_coordinate)(RANGE_3P))

    def get_language(self):
        return self.language
