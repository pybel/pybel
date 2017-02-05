# -*- coding: utf-8 -*-

"""
Protein Modifications
~~~~~~~~~~~~~~~~~~~~~

The addition of a post-translational modification (PTM) tag results in an entry called 'variants'
in the data dictionary associated with a given node. This entry is a list with dictionaries
describing each of the variants. All variants have the entry 'kind' to identify whether it is
a PTM, gene modification, fragment, or HGVS variant. The 'kind' value for PTM is 'pmod'.

Each PMOD contains an identifier, which is a dictionary with the namespace and name, and can
optionally include the position ('pos') and/or amino acid code ('code').

For example, the node :code:`p(HGNC:GSK3B, pmod(P, S, 9))` is represented with the following:

.. code::

    {
        'function': 'Protein',
        'identifier': {
            'namespace': 'HGNC',
            'name': 'GSK3B'
        },
        'variants': [
            {
                'kind': 'pmod',
                'code': 'Ser',
                'identifier': {
                    'name': 'Ph',
                    'namespace': 'PYBEL'
                },
                'pos': 9
            }
        ]
    }

.. seealso:: http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_proteinmodification_pmod
"""

import logging

from pyparsing import oneOf, MatchFirst, Group, Optional
from pyparsing import pyparsing_common as ppc

from .. import language
from ..baseparser import BaseParser, one_of_tags, nest, WCW
from ..language import pmod_namespace, pmod_legacy_labels, amino_acid
from ..parse_identifier import IdentifierParser
from ...constants import KIND, PMOD, NAMESPACE, PYBEL_DEFAULT_NAMESPACE

log = logging.getLogger(__name__)


class PmodParser(BaseParser):
    IDENTIFIER = 'identifier'
    CODE = 'code'
    POSITION = 'pos'
    ORDER = [KIND, IDENTIFIER, CODE, POSITION]

    def __init__(self, namespace_parser=None):
        """

        :param namespace_parser:
        :type namespace_parser: IdentifierParser
        :return:
        """

        self.namespace_parser = namespace_parser if namespace_parser is not None else IdentifierParser()

        pmod_tag = one_of_tags(tags=['pmod', 'proteinModification'], canonical_tag=PMOD, identifier=KIND)

        pmod_default_ns = oneOf(pmod_namespace.keys()).setParseAction(self.handle_pmod_default_ns)
        pmod_legacy_ns = oneOf(pmod_legacy_labels.keys()).setParseAction(self.handle_pmod_legacy_ns)

        pmod_identifier = MatchFirst([
            Group(self.namespace_parser.identifier_qualified),
            Group(pmod_default_ns),
            Group(pmod_legacy_ns)
        ])

        self.language = pmod_tag + nest(pmod_identifier(self.IDENTIFIER) +
                                        Optional(
                                            WCW + amino_acid(self.CODE) + Optional(WCW + ppc.integer(self.POSITION))))

    def handle_pmod_default_ns(self, s, l, tokens):
        tokens[NAMESPACE] = PYBEL_DEFAULT_NAMESPACE
        tokens['name'] = language.pmod_namespace[tokens[0]]
        return tokens

    def handle_pmod_legacy_ns(self, s, l, tokens):
        upgraded = language.pmod_legacy_labels[tokens[0]]
        log.debug('legacy pmod() value %s upgraded to %s', s, upgraded)
        tokens['namespace'] = PYBEL_DEFAULT_NAMESPACE
        tokens['name'] = upgraded
        return tokens

    def get_language(self):
        return self.language
