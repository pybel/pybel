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
        'function': 'Gene',
        'identifier': {
            'namespace': 'HGNC',
            'name': 'GSK3B'
        },
        'variants': [
            {
                'kind': 'gmod',
                'identifier': 'Me'
            }
        ]
    }

The addition of this function does not preclude the use of all other standard functions in BEL; however, other
compilers probably won't support these standards. If you agree that this is useful, please contribute to discussion in
the OpenBEL community.
"""

from pyparsing import oneOf, Group

from .. import language
from ..baseparser import BaseParser, one_of_tags, nest
from ..parse_identifier import IdentifierParser
from ...constants import KIND, GMOD, PYBEL_DEFAULT_NAMESPACE


class GmodParser(BaseParser):
    IDENTIFIER = 'identifier'
    ORDER = [KIND, IDENTIFIER]

    def __init__(self, namespace_parser=None):
        """

        :param namespace_parser:
        :type namespace_parser: IdentifierParser
        :return:
        """

        self.namespace_parser = namespace_parser if namespace_parser is not None else IdentifierParser()

        gmod_tag = one_of_tags(tags=['gmod', 'geneModification'], canonical_tag=GMOD, identifier=KIND)

        gmod_default_ns = oneOf(language.gmod_namespace.keys()).setParseAction(self.handle_gmod_default)

        gmod_identifier = Group(self.namespace_parser.identifier_qualified) | Group(gmod_default_ns)

        gmod_1 = gmod_tag + nest(gmod_identifier(self.IDENTIFIER))

        self.language = gmod_1

    def handle_gmod_default(self, s, l, tokens):
        tokens['namespace'] = PYBEL_DEFAULT_NAMESPACE
        tokens['name'] = language.gmod_namespace[tokens[0]]
        return tokens

    def get_language(self):
        return self.language
