# -*- coding: utf-8 -*-

"""HGVS Variants.

For example, the BEL term :code:`p(HGNC:GSK3B, var(p.Gly123Arg))` is translated to the following internal DSL:

.. code-block:: python

   from pybel.dsl import Protein, Hgvs
   gsk3b_variant = Protien(namespace='HGNC', name='GSK3B', variants=Hgvs('p.Gly123Arg'))

Further, the shorthand for protein substitutions, :class:`pybel.dsl.ProteinSubstitution`, can be used to produce the
same result, as it inherits from :class:`pybel.dsl.Hgvs`:

.. code-block:: python

   from pybel.dsl import Protein, ProteinSubstitution
   gsk3b_variant = Protien(namespace='HGNC', name='GSK3B', variants=ProteinSubstitution('Gly', 123, 'Arg'))

Either way, the resulting object can be used like a dict that looks like:

.. code-block:: python

    from pybel.constants import *

    {
        FUNCTION: PROTEIN,
        NAMESPACE: 'HGNC',
        NAME: 'GSK3B',
        VARIANTS: [
            {
                KIND: HGVS,
                IDENTIFIER: 'p.Gly123Arg',
            },
        ],
    }

.. seealso::

    - BEL 2.0 specification on `variants <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_variant_var>`_
    - HGVS `conventions <http://www.hgvs.org/mutnomen/recs.html>`_
    - PyBEL module :py:class:`pybel.parser.modifiers.get_hgvs_language`
"""

from pyparsing import ParserElement, Word, alphanums

from ..utils import nest, one_of_tags, quote
from ...constants import HGVS, IDENTIFIER, KIND

__all__ = [
    'get_hgvs_language',
]

variant_tags = one_of_tags(tags=['var', 'variant'], canonical_tag=HGVS, name=KIND)
variant_characters = Word(alphanums + '._*=?>')


def get_hgvs_language() -> ParserElement:
    """Build a HGVS :class:`pyparsing.ParseElement`."""
    hgvs = (variant_characters | quote)(IDENTIFIER)
    language = variant_tags + nest(hgvs)
    return language
