# -*- coding: utf-8 -*-

import logging

from pyparsing import oneOf, Group, pyparsing_common, replaceWith

from . import language
from .baseparser import BaseParser, nest
from .language import amino_acid, pmod_namespace, pmod_legacy_labels
from .parse_identifier import IdentifierParser

log = logging.getLogger('pybel')


class PmodParser(BaseParser):
    def __init__(self, namespace_parser=None):
        """

        :param namespace_parser:
        :type namespace_parser: IdentifierParser
        :return:
        """

        self.namespace_parser = namespace_parser if namespace_parser is not None else IdentifierParser()

        pmod_tag = oneOf(['pmod', 'proteinModification'])
        pmod_tag.addParseAction(replaceWith('ProteinModification'))

        pmod_default_ns = oneOf(pmod_namespace.keys()).setParseAction(self.handle_pmod_default_ns)
        pmod_legacy_ns = oneOf(pmod_legacy_labels.keys()).setParseAction(self.handle_pmod_legacy_ns)

        pmod_identifier = Group(self.namespace_parser.identifier_qualified) | pmod_default_ns | pmod_legacy_ns

        pmod_1 = pmod_tag + nest(pmod_identifier('identifier'), amino_acid('code'), pyparsing_common.integer('pos'))
        pmod_2 = pmod_tag + nest(pmod_identifier('identifier'), amino_acid('code'))
        pmod_3 = pmod_tag + nest(pmod_identifier('identifier'))

        self.language = pmod_1 | pmod_2 | pmod_3
        self.language.setParseAction(self.handle_protein_modification)

    def handle_protein_modification(self, s, l, tokens):
        return tokens

    def handle_pmod_default_ns(self, s, l, tokens):
        return [language.pmod_namespace[tokens[0]]]

    def handle_pmod_legacy_ns(self, s, l, tokens):
        log.log(5, 'PyBEL016 legacy pmod() values: {}.'.format(s))
        return [language.pmod_legacy_labels[tokens[0]]]

    def get_language(self):
        return self.language
