# -*- coding: utf-8 -*-

"""
Truncations
~~~~~~~~~~~

Truncations in the legacy BEL 1.0 specification are automatically translated to BEL 2.0 with HGVS nomenclature.
:code:`p(HGNC:AKT1, trunc(40))` becomes :code:`p(HGNC:AKT1, var(p.40*))` and is represented with the following
dictionary:

.. code::

    {
        FUNCTION: PROTEIN,
        NAMESPACE: 'HGNC',
        NAME: 'AKT1',
        VARIANTS: [
            {
                KIND: HGVS,
                IDENTIFIER: 'p.40*'
            }
        ]
    }


Unfortunately, the HGVS nomenclature requires the encoding of the terminal amino acid which is exchanged
for a stop codon, and this information is not required by BEL 1.0. For this example, the proper encoding
of the truncation at position also includes the information that the 40th amino acid in the AKT1 is Cys. Its
BEL encoding should be :code:`p(HGNC:AKT1, var(p.Cys40*))`. Temporary support has been added to
compile these statements, but it's recommended they are upgraded by reexamining the supporting text, or
looking up the amino acid sequence.

.. seealso::
    BEL 2.0 specification on `truncations <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_variants_2>`_
"""

import logging

from pyparsing import pyparsing_common as ppc

from ..baseparser import BaseParser, one_of_tags, nest
from ...constants import HGVS, KIND, IDENTIFIER

log = logging.getLogger(__name__)

trunc_tag = one_of_tags(tags=['trunc', 'truncation'], canonical_tag=HGVS, identifier=KIND)


class TruncParser(BaseParser):
    POSITION = 'position'

    def __init__(self):
        self.language = trunc_tag + nest(ppc.integer(self.POSITION))
        self.language.setParseAction(self.handle_trunc_legacy)

        BaseParser.__init__(self, self.language)

    # FIXME this isn't correct HGVS nomenclature, but truncation isn't forward compatible without more information
    def handle_trunc_legacy(self, s, l, tokens):
        upgraded = 'p.{}*'.format(tokens[self.POSITION])
        log.warning(
            'trunc() is deprecated. Please look up reference terminal amino acid and encode with HGVS: {}'.format(s))
        tokens[IDENTIFIER] = upgraded
        del tokens[self.POSITION]
        return tokens
