# -*- coding: utf-8 -*-

"""
Gene Substitutions
~~~~~~~~~~~~~~~~~~

Gene substitutions are legacy statements defined in BEL 1.0. BEL 2.0 reccomends using HGVS strings. Luckily,
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

from ..baseparser import BaseParser, one_of_tags, nest
from ..language import dna_nucleotide
from ...constants import HGVS, KIND, IDENTIFIER

log = logging.getLogger(__name__)

gsub_tag = one_of_tags(tags=['sub', 'substitution'], canonical_tag=HGVS, identifier=KIND)


class GsubParser(BaseParser):
    REFERENCE = 'reference'
    POSITION = 'position'
    VARIANT = 'variant'

    def __init__(self):
        self.language = gsub_tag + nest(dna_nucleotide(self.REFERENCE),
                                        ppc.integer(self.POSITION),
                                        dna_nucleotide(self.VARIANT))
        self.language.setParseAction(self.handle_gsub)

        BaseParser.__init__(self, self.language)

    def handle_gsub(self, s, l, tokens):
        upgraded = 'c.{}{}>{}'.format(tokens[self.POSITION], tokens[self.REFERENCE], tokens[self.VARIANT])
        log.debug('legacy sub() %s upgraded to %s', s, upgraded)
        tokens[IDENTIFIER] = upgraded
        del tokens[self.POSITION]
        del tokens[self.REFERENCE]
        del tokens[self.VARIANT]
        return tokens
