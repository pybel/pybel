# -*- coding: utf-8 -*-

"""Truncations.

Truncations in the legacy BEL 1.0 specification are automatically translated to BEL 2.0 with HGVS nomenclature.
:code:`p(HGNC:AKT1, trunc(40))` becomes :code:`p(HGNC:AKT1, var(p.40*))` and is represented with the following
dictionary:

.. code-block:: python

    from pybel.constants import *

    {
        FUNCTION: PROTEIN,
        NAMESPACE: 'HGNC',
        NAME: 'AKT1',
        VARIANTS: [
            {
                KIND: HGVS,
                IDENTIFIER: 'p.40*',
            },
        ],
    }

Unfortunately, the HGVS nomenclature requires the encoding of the terminal amino acid which is exchanged
for a stop codon, and this information is not required by BEL 1.0. For this example, the proper encoding
of the truncation at position also includes the information that the 40th amino acid in the AKT1 is Cys. Its
BEL encoding should be :code:`p(HGNC:AKT1, var(p.Cys40*))`. Temporary support has been added to
compile these statements, but it's recommended they are upgraded by reexamining the supporting text, or
looking up the amino acid sequence.

.. seealso::

    - BEL 2.0 specification on `truncations <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_variants_2>`_
    - PyBEL module :py:class:`pybel.parser.modifiers.get_truncation_language`
"""

import logging

from pyparsing import ParserElement, pyparsing_common as ppc

from .constants import amino_acid
from ..utils import nest, one_of_tags
from ...constants import HGVS, IDENTIFIER, KIND, TRUNCATION_POSITION

__all__ = [
    'get_truncation_language',
]

log = logging.getLogger(__name__)

truncation_tag = one_of_tags(tags=['trunc', 'truncation'], canonical_tag=HGVS, name=KIND)

AMINO_ACID = 'aminoacid'


def get_truncation_language() -> ParserElement:
    """Build a parser for protein truncations."""
    l1 = truncation_tag + nest(amino_acid(AMINO_ACID) + ppc.integer(TRUNCATION_POSITION))
    l1.setParseAction(_handle_trunc)
    l2 = truncation_tag + nest(ppc.integer(TRUNCATION_POSITION))
    l2.setParseAction(_handle_trunc_legacy)
    return l1 | l2


def _handle_trunc_legacy(line, _, tokens):
    # FIXME this isn't correct HGVS nomenclature, but truncation isn't forward compatible without more information
    upgraded = 'p.{}*'.format(tokens[TRUNCATION_POSITION])
    log.warning('trunc() is deprecated. Re-encode with reference terminal amino acid in HGVS: %s', line)
    tokens[IDENTIFIER] = upgraded
    del tokens[TRUNCATION_POSITION]
    return tokens


def _handle_trunc(_, __, tokens):
    aa, position = tokens[AMINO_ACID], tokens[TRUNCATION_POSITION]
    tokens[IDENTIFIER] = 'p.{aa}{position}*'.format(aa=aa, position=position)
    del tokens[AMINO_ACID]
    del tokens[TRUNCATION_POSITION]
    return tokens
