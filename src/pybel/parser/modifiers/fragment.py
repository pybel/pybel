# -*- coding: utf-8 -*-

"""
Fragments
~~~~~~~~~

The addition of a fragment results in an entry called :py:data:`VARIANTS`
in the data dictionary associated with a given node. This entry is a list with dictionaries
describing each of the variants. All variants have the entry :py:data:`KIND` to identify whether it is
a PTM, gene modification, fragment, or HGVS variant. The :py:data:`KIND` value for a fragment is :py:data:`FRAGMENT`.

Each fragment contains an identifier, which is a dictionary with the namespace and name, and can
optionally include the position ('pos') and/or amino acid code ('code').

For example, the node :code:`p(HGNC:GSK3B, frag(45_129))` is represented with the following:

.. code::

    {
        FUNCTION: PROTEIN,
        NAMESPACE: 'HGNC',
        NAME: 'GSK3B',
        VARIANTS: [
            {
                KIND: FRAGMENT,
                FragmentParser.START: 45,
                FragmentParser.STOP: 129
            }
        ]
    }

Additionally, nodes can have an asterick (*) or question mark (?) representing unbound
or unknown fragments, respectively.

A fragment may also be unknown, such as in the node :code:`p(HGNC:GSK3B, frag(?))`. This
is represented with the key :py:data:`FragmentParser.MISSING` and the value of '?' like:


.. code::

    {
        FUNCTION: PROTEIN,
        NAMESPACE: 'HGNC',
        NAME: 'GSK3B',
        VARIANTS: [
            {
                KIND: FRAGMENT,
                FragmentParser.MISSING: '?',
            }
        ]
    }

.. seealso::

   BEL 2.0 specification on `proteolytic fragments (2.2.3) <http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_proteolytic_fragments>`_
"""

from pyparsing import pyparsing_common as ppc, Keyword, Optional

from ..baseparser import BaseParser, one_of_tags, nest, WCW, word
from ...constants import FRAGMENT, KIND

fragment_tag = one_of_tags(tags=['frag', 'fragment'], canonical_tag=FRAGMENT, identifier=KIND)


class FragmentParser(BaseParser):
    START = 'start'
    STOP = 'stop'
    MISSING = 'missing'
    DESCRIPTION = 'description'

    def __init__(self):
        self.fragment_range = (ppc.integer | '?')(self.START) + '_' + (ppc.integer | '?' | '*')(self.STOP)
        self.missing_fragment = Keyword('?')(self.MISSING)

        self.language = fragment_tag + nest(
            (self.fragment_range | self.missing_fragment(self.MISSING)) + Optional(
                WCW + word(self.DESCRIPTION)))

        BaseParser.__init__(self, self.language)
