# -*- coding: utf-8 -*-

"""
Protein Substitutions
~~~~~~~~~~~~~~~~~~~~~

Protein substitutions are legacy statements defined in BEL 1.0. BEL 2.0 recommends using HGVS strings. Luckily,
the information contained in a BEL 1.0 encoding, such as :code:`p(HGNC:APP,sub(R,275,H))` can be
automatically translated to the appropriate HGVS :code:`p(HGNC:APP, var(p.Arg275His))`, assuming that all
substitutions are using the reference protein sequence for numbering and not the genomic reference.
The previous statements both produce the underlying data:

.. code::

    {
        'function': 'Protein',
        'identifier': {
            'namespace': 'HGNC',
            'name': 'APP'
        },
        'variants': [
            {
                'kind': 'hgvs',
                'identifier': 'p.Arg275His'
            }
        ]
    }

.. seealso:: http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_variants_2
"""

import logging

from pyparsing import pyparsing_common as ppc

from .variant import VariantParser
from ..baseparser import BaseParser, one_of_tags, nest
from ..language import amino_acid
from ...constants import HGVS, KIND

log = logging.getLogger(__name__)


class PsubParser(BaseParser):
    REFERENCE = 'reference'
    POSITION = 'position'
    VARIANT = 'variant'

    def __init__(self):
        psub_tag = one_of_tags(tags=['sub', 'substitution'], canonical_tag=HGVS, identifier=KIND)
        self.language = psub_tag + nest(amino_acid(self.REFERENCE),
                                        ppc.integer(self.POSITION),
                                        amino_acid(self.VARIANT))
        self.language.setParseAction(self.handle_psub)

    def handle_psub(self, s, l, tokens):
        upgraded = 'p.{}{}{}'.format(tokens[self.REFERENCE], tokens[self.POSITION], tokens[self.VARIANT])
        log.log(5, 'sub() in p() is deprecated: %s. Upgraded to %s', s, upgraded)
        tokens[VariantParser.IDENTIFIER] = upgraded
        del tokens[self.REFERENCE]
        del tokens[self.POSITION]
        del tokens[self.VARIANT]
        return tokens

    def get_language(self):
        return self.language
