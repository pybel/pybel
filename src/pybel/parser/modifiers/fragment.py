# -*- coding: utf-8 -*-

"""
Fragments
~~~~~~~~~

The addition of a fragment results in an entry called :data:`pybel.constants.VARIANTS`
in the data dictionary associated with a given node. This entry is a list with dictionaries
describing each of the variants. All variants have the entry :data:`pybel.constants.KIND` to identify whether it is
a PTM, gene modification, fragment, or HGVS variant. The :data:`pybel.constants.KIND` value for a fragment is
:data:`pybel.constants.FRAGMENT`.

Each fragment contains an identifier, which is a dictionary with the namespace and name, and can optionally include
the position ('pos') and/or amino acid code ('code').

For example, the node :code:`p(HGNC:GSK3B, frag(45_129))` is represented with the following:

.. code::

    {
        FUNCTION: PROTEIN,
        NAMESPACE: 'HGNC',
        NAME: 'GSK3B',
        VARIANTS: [
            {
                KIND: FRAGMENT,
                FRAGMENT_START: 45,
                FRAGMENT_STOP: 129
            }
        ]
    }

Additionally, nodes can have an asterick (*) or question mark (?) representing unbound
or unknown fragments, respectively.

A fragment may also be unknown, such as in the node :code:`p(HGNC:GSK3B, frag(?))`. This
is represented with the key :data:`pybel.constants.FRAGMENT_MISSING` and the value of '?' like:


.. code::

    {
        FUNCTION: PROTEIN,
        NAMESPACE: 'HGNC',
        NAME: 'GSK3B',
        VARIANTS: [
            {
                KIND: FRAGMENT,
                FRAGMENT_MISSING: '?',
            }
        ]
    }

.. seealso::

    - BEL 2.0 specification on `proteolytic fragments (2.2.3) <http://openbel.org/language/version_2.0/bel_specification_version_2.0.html#_proteolytic_fragments>`_
    - PyBEL module :py:class:`pybel.parser.modifiers.FragmentParser`
"""

from pyparsing import And, Keyword, Optional, Suppress, pyparsing_common as ppc

from ..baseparser import BaseParser
from ..utils import WCW, nest, one_of_tags, quote
from ...constants import FRAGMENT, FRAGMENT_DESCRIPTION, FRAGMENT_MISSING, FRAGMENT_START, FRAGMENT_STOP, KIND

__all__ = [
    'fragment_tag',
    'FragmentParser',
]

fragment_tag = one_of_tags(tags=['frag', 'fragment'], canonical_tag=FRAGMENT, name=KIND)


class FragmentParser(BaseParser):
    def __init__(self):
        self.fragment_range = (ppc.integer | '?')(FRAGMENT_START) + '_' + (ppc.integer | '?' | '*')(FRAGMENT_STOP)
        self.missing_fragment = Keyword('?')(FRAGMENT_MISSING)

        self._fragment_value_inner = self.fragment_range | self.missing_fragment(FRAGMENT_MISSING)

        self._fragment_value = (
                self._fragment_value_inner |
                And([Suppress('"'), self._fragment_value_inner, Suppress('"')])
        )

        self.language = fragment_tag + nest(self._fragment_value + Optional(WCW + quote(FRAGMENT_DESCRIPTION)))

        super(FragmentParser, self).__init__(self.language)
