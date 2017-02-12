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
        FUNCTION: PROTEIN,
        NAMESPACE: 'HGNC',
        NAME: 'GSK3B',
        VARIANTS: [
            {
                KIND: PMOD,
                IDENTIFIER: {
                    NAMESPACE: BEL_DEFAULT_NAMESPACE
                    NAME: 'Ph',

                },
                PmodParser.CODE: 'Ser',
                PmodParser.POSITION: 9
            }
        ]
    }


As an additional example, in :code:`p(HGNC:MAPK1, pmod(Ph, Thr, 202), pmod(Ph, Tyr, 204))`, MAPK is phosphorylated
twice to become active. This results in the following:

.. code::

    {
        FUNCTION: PROTEIN,
        NAMESPACE: 'HGNC',
        NAME: 'MAPK1',
        VARIANTS: [
            {
                KIND: PMOD,
                IDENTIFIER: {
                    NAMESPACE: BEL_DEFAULT_NAMESPACE
                    NAME: 'Ph',

                },
                PmodParser.CODE: 'Thr',
                PmodParser.POSITION: 202
            },
            {
                KIND: PMOD,
                IDENTIFIER: {
                    NAMESPACE: BEL_DEFAULT_NAMESPACE
                    NAME: 'Ph',

                },
                PmodParser.CODE: 'Tyr',
                PmodParser.POSITION: 204
            }
        ]
    }

.. seealso::

    BEL 2.0 specification on `protein modifications <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_proteinmodification_pmod>`_
"""

import logging

from pyparsing import oneOf, MatchFirst, Group, Optional
from pyparsing import pyparsing_common as ppc

from .. import language
from ..baseparser import BaseParser, one_of_tags, nest, WCW
from ..language import pmod_namespace, pmod_legacy_labels, amino_acid
from ..parse_identifier import IdentifierParser
from ...constants import KIND, PMOD, NAMESPACE, BEL_DEFAULT_NAMESPACE, IDENTIFIER

log = logging.getLogger(__name__)

pmod_tag = one_of_tags(tags=['pmod', 'proteinModification'], canonical_tag=PMOD, identifier=KIND)


class PmodParser(BaseParser):
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

        pmod_default_ns = oneOf(pmod_namespace.keys()).setParseAction(self.handle_pmod_default_ns)
        pmod_legacy_ns = oneOf(pmod_legacy_labels.keys()).setParseAction(self.handle_pmod_legacy_ns)

        pmod_identifier = MatchFirst([
            Group(self.namespace_parser.identifier_qualified),
            Group(pmod_default_ns),
            Group(pmod_legacy_ns)
        ])

        self.language = pmod_tag + nest(pmod_identifier(IDENTIFIER) + Optional(
            WCW + amino_acid(self.CODE) + Optional(WCW + ppc.integer(self.POSITION))))

        BaseParser.__init__(self, self.language)

    def handle_pmod_default_ns(self, s, l, tokens):
        tokens[NAMESPACE] = BEL_DEFAULT_NAMESPACE
        tokens['name'] = language.pmod_namespace[tokens[0]]
        return tokens

    def handle_pmod_legacy_ns(self, s, l, tokens):
        upgraded = language.pmod_legacy_labels[tokens[0]]
        log.debug('legacy pmod() value %s upgraded to %s', s, upgraded)
        tokens['namespace'] = BEL_DEFAULT_NAMESPACE
        tokens['name'] = upgraded
        return tokens
