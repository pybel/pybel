# -*- coding: utf-8 -*-

"""Gene Substitutions.

Gene substitutions are legacy statements defined in BEL 1.0. BEL 2.0 recommends using HGVS strings. Luckily,
the information contained in a BEL 1.0 encoding, such as :code:`g(HGNC:APP,sub(G,275341,C))` can be
automatically translated to the appropriate HGVS :code:`g(HGNC:APP, var(c.275341G>C))`, assuming that all
substitutions are using the reference coding gene sequence for numbering and not the genomic reference.
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
                IDENTIFIER: 'c.275341G>C',
            },
        ],
    }

.. seealso::

    - BEL 2.0 specification on `gene substitutions <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_variants_2>`_
    - PyBEL module :py:class:`pybel.parser.modifiers.get_gene_substitution_language`
"""

import logging

from pyparsing import ParserElement, oneOf, pyparsing_common as ppc

from ..utils import nest, one_of_tags
from ... import language
from ...constants import GSUB_POSITION, GSUB_REFERENCE, GSUB_VARIANT, HGVS, IDENTIFIER, KIND

__all__ = [
    'get_gene_substitution_language',
]

log = logging.getLogger(__name__)

dna_nucleotide = oneOf(list(language.dna_nucleotide_labels.keys()))
gsub_tag = one_of_tags(tags=['sub', 'substitution'], canonical_tag=HGVS, name=KIND)


def get_gene_substitution_language() -> ParserElement:
    """Build a gene substitution parser."""
    parser_element = gsub_tag + nest(
        dna_nucleotide(GSUB_REFERENCE),
        ppc.integer(GSUB_POSITION),
        dna_nucleotide(GSUB_VARIANT),
    )
    parser_element.setParseAction(_handle_gsub)
    return parser_element


def _handle_gsub(line, _, tokens):
    upgraded = 'c.{}{}>{}'.format(tokens[GSUB_POSITION], tokens[GSUB_REFERENCE], tokens[GSUB_VARIANT])
    log.debug('legacy sub() %s upgraded to %s', line, upgraded)
    tokens[IDENTIFIER] = upgraded
    del tokens[GSUB_POSITION]
    del tokens[GSUB_REFERENCE]
    del tokens[GSUB_VARIANT]
    return tokens
