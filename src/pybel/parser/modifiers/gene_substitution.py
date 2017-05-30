# -*- coding: utf-8 -*-

"""
Gene Substitutions
~~~~~~~~~~~~~~~~~~

Gene substitutions are legacy statements defined in BEL 1.0. BEL 2.0 recommends using HGVS strings. Luckily,
the information contained in a BEL 1.0 encoding, such as :code:`g(HGNC:APP,sub(G,275341,C))` can be
automatically translated to the appropriate HGVS :code:`g(HGNC:APP, var(c.275341G>C))`, assuming that all
substitutions are using the reference coding gene sequence for numbering and not the genomic reference.
The previous statements both produce the underlying data:

.. code::

    {
        FUNCTION: GENE,
        NAMESPACE: 'HGNC',
        NAME: 'APP',
        VARIANTS: [
            {
                KIND: HGVS,
                IDENTIFIER: 'c.275341G>C'
            }
        ]
    }

.. seealso::

    BEL 2.0 specification on `gene substitutions <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_variants_2>`_
"""

import logging

from pyparsing import pyparsing_common as ppc

from ..baseparser import BaseParser
from ..language import dna_nucleotide
from ..utils import nest, one_of_tags
from ...constants import GSUB_REFERENCE, GSUB_POSITION, GSUB_VARIANT, HGVS, KIND, IDENTIFIER

__all__ = [
    'gsub_tag',
    'GsubParser',
]

log = logging.getLogger(__name__)

gsub_tag = one_of_tags(tags=['sub', 'substitution'], canonical_tag=HGVS, identifier=KIND)


class GsubParser(BaseParser):
    def __init__(self):
        self.language = gsub_tag + nest(dna_nucleotide(GSUB_REFERENCE),
                                        ppc.integer(GSUB_POSITION),
                                        dna_nucleotide(GSUB_VARIANT))
        self.language.setParseAction(self.handle_gsub)

        super(GsubParser, self).__init__(self.language)

    def handle_gsub(self, line, position, tokens):
        upgraded = 'c.{}{}>{}'.format(tokens[GSUB_POSITION], tokens[GSUB_REFERENCE], tokens[GSUB_VARIANT])
        log.debug('legacy sub() %s upgraded to %s', line, upgraded)
        tokens[IDENTIFIER] = upgraded
        del tokens[GSUB_POSITION]
        del tokens[GSUB_REFERENCE]
        del tokens[GSUB_VARIANT]
        return tokens
