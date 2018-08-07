# -*- coding: utf-8 -*-

"""
HGVS Variants
~~~~~~~~~~~~~
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

    - BEL 2.0 specification on `variants <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_variant_var>`_
    - HVGS `conventions <http://www.hgvs.org/mutnomen/recs.html>`_
    - PyBEL module :py:class:`pybel.parser.modifiers.get_hgvs_language`
"""

from pyparsing import Word, alphanums

from ..utils import nest, one_of_tags, quote
from ...constants import HGVS, IDENTIFIER, KIND

__all__ = [
    'get_hgvs_language',
]

variant_tags = one_of_tags(tags=['var', 'variant'], canonical_tag=HGVS, name=KIND)
variant_characters = Word(alphanums + '._*=?>')


def get_hgvs_language():
    """

    :rtype: pyparsing.ParseElement
    """
    hgvs = (variant_characters | quote)(IDENTIFIER)
    language = variant_tags + nest(hgvs)
    return language
