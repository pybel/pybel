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

from pyparsing import oneOf, replaceWith, pyparsing_common, Keyword, Suppress, Group

from ..baseparser import BaseParser, nest
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
