# -*- coding: utf-8 -*-

"""Gene Modifications.

PyBEL introduces the gene modification tag, gmod(), to allow for the encoding of epigenetic modifications.
Its syntax follows the same style s the pmod() tags for proteins, and can include the following values:

- M
- Me
- methylation
- A
- Ac
- acetylation

For example, the node :code:`g(HGNC:GSK3B, gmod(M))` is represented with the following:

.. code-block:: python

    from pybel.constants import *

    {
        FUNCTION: GENE,
        NAMESPACE: 'HGNC',
        NAME: 'GSK3B',
        VARIANTS: [
            {
                KIND: GMOD,
                IDENTIFIER: {
                    NAMESPACE: BEL_DEFAULT_NAMESPACE,
                    NAME: 'Me',
                },
            },
        ],
    }

The addition of this function does not preclude the use of all other standard functions in BEL; however, other
compilers probably won't support these standards. If you agree that this is useful, please contribute to discussion
in the OpenBEL community.

.. seealso::

    - PyBEL module :py:func:`pybel.parser.modifiers.get_gene_modification_language`
"""

from pyparsing import Group, MatchFirst, ParserElement, oneOf

from ..utils import nest, one_of_tags
from ...constants import BEL_DEFAULT_NAMESPACE, GMOD, IDENTIFIER, KIND, NAME, NAMESPACE
from ...language import gmod_namespace

__all__ = [
    'get_gene_modification_language',
]


def _handle_gmod_default(_, __, tokens):
    tokens[NAMESPACE] = BEL_DEFAULT_NAMESPACE
    tokens[NAME] = gmod_namespace[tokens[0]]
    return tokens


gmod_tag = one_of_tags(tags=['gmod', 'geneModification'], canonical_tag=GMOD, name=KIND)
gmod_default_ns = oneOf(list(gmod_namespace)).setParseAction(_handle_gmod_default)


def get_gene_modification_language(identifier_qualified: ParserElement) -> ParserElement:
    """Build a gene modification parser."""
    gmod_identifier = MatchFirst([
        identifier_qualified,
        gmod_default_ns,
    ])

    return gmod_tag + nest(
        Group(gmod_identifier)(IDENTIFIER)
    )
