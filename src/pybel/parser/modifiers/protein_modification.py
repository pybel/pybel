# -*- coding: utf-8 -*-

"""Protein Modifications.

The addition of a post-translational modification (PTM) tag results in an entry called 'variants'
in the data dictionary associated with a given node. This entry is a list with dictionaries
describing each of the variants. All variants have the entry 'kind' to identify whether it is
a PTM, gene modification, fragment, or HGVS variant. The 'kind' value for PTM is 'pmod'.

Each PMOD contains an identifier, which is a dictionary with the namespace and name, and can
optionally include the position ('pos') and/or amino acid code ('code').

For example, the node :code:`p(HGNC:GSK3B, pmod(P, S, 9))` is represented with the following:

.. code-block:: python

    from pybel.constants import *

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
                PMOD_POSITION: 9,
            },
        ],
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

   - BEL 2.0 specification on `protein modifications
     <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_proteinmodification_pmod>`_
   - PyBEL module :py:class:`pybel.parser.modifiers.get_protein_modification_language`
"""

import logging

from pyparsing import Group, MatchFirst, Optional, ParseResults, ParserElement, oneOf, pyparsing_common as ppc

from .constants import amino_acid
from ..utils import WCW, nest, one_of_tags
from ...constants import BEL_DEFAULT_NAMESPACE, IDENTIFIER, KIND, NAME, NAMESPACE, PMOD, PMOD_CODE, PMOD_POSITION
from ...language import pmod_legacy_labels, pmod_namespace

__all__ = [
    'get_protein_modification_language',
]

log = logging.getLogger(__name__)


def _handle_pmod_default_ns(_, __, tokens: ParseResults) -> ParseResults:
    tokens[NAMESPACE] = BEL_DEFAULT_NAMESPACE
    tokens[NAME] = pmod_namespace[tokens[0]]
    return tokens


def _handle_pmod_legacy_ns(line, _, tokens: ParseResults) -> ParseResults:
    upgraded = pmod_legacy_labels[tokens[0]]
    log.log(5, 'legacy pmod() value %s upgraded to %s', line, upgraded)
    tokens[NAMESPACE] = BEL_DEFAULT_NAMESPACE
    tokens[NAME] = upgraded
    return tokens


pmod_tag = one_of_tags(tags=['pmod', 'proteinModification'], canonical_tag=PMOD, name=KIND)
pmod_default_ns = oneOf(list(pmod_namespace)).setParseAction(_handle_pmod_default_ns)
pmod_legacy_ns = oneOf(list(pmod_legacy_labels)).setParseAction(_handle_pmod_legacy_ns)


def get_protein_modification_language(identifier_qualified: ParserElement) -> ParserElement:
    """Build a protein modification parser."""
    pmod_identifier = MatchFirst([
        identifier_qualified,
        pmod_default_ns,
        pmod_legacy_ns
    ])

    return pmod_tag + nest(
        Group(pmod_identifier)(IDENTIFIER) +
        Optional(
            WCW +
            amino_acid(PMOD_CODE) +
            Optional(
                WCW +
                ppc.integer(PMOD_POSITION)
            )
        )
    )
