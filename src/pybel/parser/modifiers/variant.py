# -*- coding: utf-8 -*-

"""
Variants
~~~~~~~~

The addition of a variant tag results in an entry called 'variants' in the data dictionary associated with a given
node. This entry is a list with dictionaries describing each of the variants. All variants have the entry 'kind' to
identify whether it is a PTM, gene modification, fragment, or HGVS variant. The 'kind' value for a variant
is 'hgvs', but best described by :data:`pybel.constants.HGVS`


For example, the node :code:`p(HGNC:GSK3B, var(p.Gly123Arg))` is represented with the following:

.. code::

   {
        FUNCTION: PROTEIN,
        NAMESPACE: 'HGNC',
        NAME: 'GSK3B',
        VARIANTS:  [
            {
               KIND: HGVS,
               IDENTIFIER: 'p.Gly123Arg'
            }
       ]
   }


.. seealso::

    - BEL 2.0 specification on `variants <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_variant_var>`_
    - HVGS `conventions <http://www.hgvs.org/mutnomen/recs.html>`_
"""

from pyparsing import Word, alphanums

from ..baseparser import BaseParser
from ..utils import quote, nest, one_of_tags
from ...constants import HGVS, KIND, IDENTIFIER

variant_tags = one_of_tags(tags=['var', 'variant'], canonical_tag=HGVS, identifier=KIND)
variant_characters = Word(alphanums + '._*=?>')


class VariantParser(BaseParser):
    def __init__(self):
        self.language = variant_tags + nest((variant_characters | quote)(IDENTIFIER))

        super(VariantParser, self).__init__(self.language)
