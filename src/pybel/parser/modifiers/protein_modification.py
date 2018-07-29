# -*- coding: utf-8 -*-

"""
Protein Modification
~~~~~~~~~~~~~~~~~~~~

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
               PMOD_CODE: 'Ser',
               PMOD_POSITION: 9
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
               PMOD_CODE: 'Thr',
               PMOD_POSITION: 202
           },
           {
               KIND: PMOD,
               IDENTIFIER: {
                   NAMESPACE: BEL_DEFAULT_NAMESPACE
                   NAME: 'Ph',

               },
               PMOD_CODE: 'Tyr',
               PMOD_POSITION: 204
           }
       ]
   }

.. seealso::

   - BEL 2.0 specification on `protein modifications <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_proteinmodification_pmod>`_
   - PyBEL module :py:class:`pybel.parser.modifiers.ProteinModificationParser`
"""

import logging

from pyparsing import Group, MatchFirst, Optional, oneOf, pyparsing_common as ppc

from .constants import amino_acid
from ..baseparser import BaseParser
from ..parse_identifier import IdentifierParser
from ..utils import WCW, nest, one_of_tags
from ... import language
from ...constants import (
    BEL_DEFAULT_NAMESPACE, IDENTIFIER, KIND, NAMESPACE, PMOD, PMOD_CODE, PMOD_POSITION,
)

__all__ = [
    'pmod_tag',
    'ProteinModificationParser',
    'amino_acid',
]

log = logging.getLogger(__name__)

pmod_tag = one_of_tags(tags=['pmod', 'proteinModification'], canonical_tag=PMOD, name=KIND)


class ProteinModificationParser(BaseParser):
    def __init__(self, identifier_parser=None):
        """
        :param IdentifierParser identifier_parser: An identifier parser for checking the 3P and 5P partners
        """
        self.identifier_parser = identifier_parser if identifier_parser is not None else IdentifierParser()

        pmod_default_ns = oneOf(list(language.pmod_namespace.keys())).setParseAction(self.handle_pmod_default_ns)
        pmod_legacy_ns = oneOf(list(language.pmod_legacy_labels.keys())).setParseAction(self.handle_pmod_legacy_ns)

        pmod_identifier = MatchFirst([
            Group(self.identifier_parser.identifier_qualified),
            Group(pmod_default_ns),
            Group(pmod_legacy_ns)
        ])

        self.language = pmod_tag + nest(pmod_identifier(IDENTIFIER) + Optional(
            WCW + amino_acid(PMOD_CODE) + Optional(WCW + ppc.integer(PMOD_POSITION))))

        super(ProteinModificationParser, self).__init__(self.language)

    @staticmethod
    def handle_pmod_default_ns(line, position, tokens):
        tokens[NAMESPACE] = BEL_DEFAULT_NAMESPACE
        tokens['name'] = language.pmod_namespace[tokens[0]]
        return tokens

    @staticmethod
    def handle_pmod_legacy_ns(line, position, tokens):
        upgraded = language.pmod_legacy_labels[tokens[0]]
        log.log(5, 'legacy pmod() value %s upgraded to %s', line, upgraded)
        tokens['namespace'] = BEL_DEFAULT_NAMESPACE
        tokens['name'] = upgraded
        return tokens
