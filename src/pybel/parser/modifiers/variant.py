# -*- coding: utf-8 -*-

"""
Variants
~~~~~~~~

The addition of a variant tag results in an entry called 'variants' in the data dictionary associated with a given
node. This entry is a list with dictionaries describing each of the variants. All variants have the entry 'kind' to
identify whether it is a PTM, gene modification, fragment, or HGVS variant. The 'kind' value for a variant
is 'hgvs', but best descirbed by :code:`pybel.constants.HGVS`


For example, the node :code:`p(HGNC:GSK3B, var(p.Gly123Arg))` is represented with the following:

.. code::

   {
       'function': 'Protein',
       'identifier': {
           'namespace': 'HGNC',
           'name': 'GSK3B'
       },
       'variants': [
           {
               'kind': 'hgvs',
               'identifier': 'p.Gly123Arg'
           }
       ]
   }


.. seealso::

    - http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_variant_var
    - HVGS for conventions http://www.hgvs.org/mutnomen/recs.html
"""

from pyparsing import Word, alphanums

from ..baseparser import BaseParser, one_of_tags, nest
from ...constants import HGVS, KIND


class VariantParser(BaseParser):
    IDENTIFIER = 'identifier'

    def __init__(self):
        variant_tags = one_of_tags(tags=['var', 'variant'], canonical_tag=HGVS, identifier=KIND)
        variant_characters = Word(alphanums + '._*=?>')
        self.language = variant_tags + nest(variant_characters(self.IDENTIFIER))

    def get_language(self):
        return self.language
