# -*- coding: utf-8 -*-

"""
Gene Modifications
~~~~~~~~~~~~~~~~~~

PyBEL introduces the gene modification tag, gmod(), to allow for the encoding of epigenetic modifications.
Its syntax follows the same style s the pmod() tags for proteins, and can include the following values:

- M
- Me
- methylation
- A
- Ac
- acetylation

For example, the node :code:`g(HGNC:GSK3B, gmod(M))` is represented with the following:

.. code::

    {
        FUNCTION: GENE,
        NAMESPACE: 'HGNC',
        NAME: 'GSK3B',
        VARIANTS: [
            {
                KIND: GMOD,
                IDENTIFIER: {
                    NAMESPACE: BEL_DEFAULT_NAMESPACE,
                    NAME: 'Me'
                }
            }
        ]
    }

The addition of this function does not preclude the use of all other standard functions in BEL; however, other
compilers probably won't support these standards. If you agree that this is useful, please contribute to discussion in
the OpenBEL community.
"""

from pyparsing import oneOf, Group

from .. import language
from ..baseparser import BaseParser
from ..parse_identifier import IdentifierParser
from ..utils import nest, one_of_tags
from ...constants import KIND, GMOD, BEL_DEFAULT_NAMESPACE, IDENTIFIER, NAME, NAMESPACE

__all__ = [
    'gmod_tag',
    'GmodParser',
]

gmod_tag = one_of_tags(tags=['gmod', 'geneModification'], canonical_tag=GMOD, identifier=KIND)


class GmodParser(BaseParser):
    def __init__(self, identifier_parser=None):
        """
        :param IdentifierParser identifier_parser: An identifier parser for checking the 3P and 5P partners
        """
        self.namespace_parser = identifier_parser if identifier_parser is not None else IdentifierParser()

        gmod_default_ns = oneOf(list(language.gmod_namespace.keys())).setParseAction(self.handle_gmod_default)

        gmod_identifier = Group(self.namespace_parser.identifier_qualified) | Group(gmod_default_ns)

        self.language = gmod_tag + nest(gmod_identifier(IDENTIFIER))

        super(GmodParser, self).__init__(self.language)

    def handle_gmod_default(self, line, position, tokens):
        tokens[NAMESPACE] = BEL_DEFAULT_NAMESPACE
        tokens[NAME] = language.gmod_namespace[tokens[0]]
        return tokens
