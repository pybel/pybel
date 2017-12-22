# -*- coding: utf-8 -*-

"""
Gene Modification
~~~~~~~~~~~~~~~~~

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
compilers probably won't support these standards. If you agree that this is useful, please contribute to discussion
in the OpenBEL community.

.. seealso::

    - PyBEL module :py:class:`pybel.parser.modifiers.GeneModificationParser`
"""

from pyparsing import Group, oneOf

from ..baseparser import BaseParser
from ..parse_identifier import IdentifierParser
from ..utils import nest, one_of_tags
from ... import language
from ...constants import BEL_DEFAULT_NAMESPACE, GMOD, IDENTIFIER, KIND, NAME, NAMESPACE

__all__ = [
    'gmod_tag',
    'GeneModificationParser',
]

gmod_tag = one_of_tags(tags=['gmod', 'geneModification'], canonical_tag=GMOD, name=KIND)


class GeneModificationParser(BaseParser):
    def __init__(self, identifier_parser=None):
        """
        :param IdentifierParser identifier_parser: An identifier parser for checking the 3P and 5P partners
        """
        self.identifier_parser = identifier_parser if identifier_parser is not None else IdentifierParser()

        gmod_default_ns = oneOf(list(language.gmod_namespace.keys())).setParseAction(self.handle_gmod_default)

        gmod_identifier = Group(self.identifier_parser.identifier_qualified) | Group(gmod_default_ns)

        self.language = gmod_tag + nest(gmod_identifier(IDENTIFIER))

        super(GeneModificationParser, self).__init__(self.language)

    @staticmethod
    def handle_gmod_default(line, position, tokens):
        tokens[NAMESPACE] = BEL_DEFAULT_NAMESPACE
        tokens[NAME] = language.gmod_namespace[tokens[0]]
        return tokens
