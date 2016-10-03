from pyparsing import oneOf, Group, pyparsing_common

from . import language
from .baseparser import BaseParser, WCW, RP, LP
from .parse_namespace import NamespaceParser


class PmodParser(BaseParser):
    def __init__(self, namespace_parser=None):
        """

        :param namespace_parser:
        :type namespace_parser: NamespaceParser
        :return:
        """

        self.namespace_parser = namespace_parser if namespace_parser is not None else NamespaceParser()

        aa_single = oneOf(language.amino_acid_dict.keys())
        aa_triple = oneOf(language.amino_acid_dict.values())

        amino_acids = aa_triple | aa_single

        pmod_tag = oneOf(['pmod', 'proteinModification'])
        pmod_default_ns = oneOf(language.pmod_namespace)
        pmod_legacy_ns = oneOf(language.pmod_legacy_labels.keys())

        pmod_val = Group(self.namespace_parser.namespace_qualified) | pmod_default_ns | pmod_legacy_ns

        pmod_option_1 = pmod_tag + LP + pmod_val + WCW + amino_acids + WCW + pyparsing_common.integer() + RP
        pmod_option_2 = pmod_tag + LP + pmod_val + WCW + amino_acids + RP
        pmod_option_3 = pmod_tag + LP + pmod_val + RP

        self.language = pmod_option_1 | pmod_option_2 | pmod_option_3
        self.language.setParseAction(self.handle_protein_modification)

    def handle_protein_modification(self, s, l, tokens):
        tokens[0] = 'ProteinModification'
        return tokens

    def handle_pmod_default_ns(self, s, l, tokens):
        # TODO implement
        return tokens

    def handle_pmod_legacy_ns(self, s, l, tokens):
        # TODO implement
        return tokens

    def get_language(self):
        return self.language
