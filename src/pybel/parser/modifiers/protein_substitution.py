# -*- coding: utf-8 -*-

"""Protein Substitutions.

Protein substitutions are legacy statements defined in BEL 1.0. BEL 2.0 recommends using HGVS strings. Luckily,
the information contained in a BEL 1.0 encoding, such as :code:`p(HGNC:APP,sub(R,275,H))` can be
automatically translated to the appropriate HGVS :code:`p(HGNC:APP, var(p.Arg275His))`, assuming that all
substitutions are using the reference protein sequence for numbering and not the genomic reference.
The previous statements both produce the underlying data:

.. code-block:: python

    from pybel.constants import *

    {
        FUNCTION: GENE,
        NAMESPACE: 'HGNC',
        NAME: 'APP',
        VARIANTS: [
            {
                KIND: HGVS,
                IDENTIFIER: 'p.Arg275His',
            },
        ],
    }

.. seealso::

    - BEL 2.0 specification on `protein substitutions
      <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_variants_2>`_
    - PyBEL module :py:class:`pybel.parser.modifiers.get_protein_substitution_language`
"""

import logging

from pyparsing import ParserElement, pyparsing_common as ppc

from .constants import amino_acid
from ..utils import nest, one_of_tags
from ...constants import (
    HGVS, IDENTIFIER, KIND, PSUB_POSITION, PSUB_REFERENCE, PSUB_VARIANT,
)

__all__ = [
    'get_protein_substitution_language',
]

log = logging.getLogger(__name__)

psub_tag = one_of_tags(tags=['sub', 'substitution'], canonical_tag=HGVS, name=KIND)


def get_protein_substitution_language() -> ParserElement:
    """Build a protein substitution parser."""
    parser_element = psub_tag + nest(
        amino_acid(PSUB_REFERENCE),
        ppc.integer(PSUB_POSITION),
        amino_acid(PSUB_VARIANT),
    )
    parser_element.setParseAction(_handle_psub)
    return parser_element


def _handle_psub(line, _, tokens):
    upgraded = 'p.{}{}{}'.format(tokens[PSUB_REFERENCE], tokens[PSUB_POSITION], tokens[PSUB_VARIANT])
    log.log(5, 'sub() in p() is deprecated: %s. Upgraded to %s', line, upgraded)
    tokens[IDENTIFIER] = upgraded
    del tokens[PSUB_REFERENCE]
    del tokens[PSUB_POSITION]
    del tokens[PSUB_VARIANT]
    return tokens
