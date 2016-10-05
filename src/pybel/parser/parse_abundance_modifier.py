import logging

from pyparsing import *

from .baseparser import BaseParser, LP, RP, WCW, word, nest
from .language import aa_triple, amino_acid, dna_nucleotide, dna_nucleotide_labels, rna_nucleotide_labels
from .parse_identifier import IdentifierParser

log = logging.getLogger(__name__)

dna_nucleotide_seq = Word(''.join(dna_nucleotide_labels.keys()))
rna_nucleotide_seq = Word(''.join(rna_nucleotide_labels.keys()))

hgvs_rna_del = (Suppress('r.') + pyparsing_common.integer() +
                Suppress('_') + pyparsing_common.integer() + 'del' +
                rna_nucleotide_seq)

hgvs_dna_del = (Suppress('c.') + pyparsing_common.integer() +
                Suppress('_') + pyparsing_common.integer() + 'del' +
                dna_nucleotide_seq)

hgvs_chromosome = (Suppress('g.') + pyparsing_common.integer() +
                   Suppress('_') + pyparsing_common.integer() + 'del' +
                   dna_nucleotide_seq)

hgvs_snp = 'del' + dna_nucleotide_seq

hgvs_protein_del = Suppress('p.') + aa_triple + pyparsing_common.integer() + 'del'

hgvs_protein_mut = Suppress('p.') + aa_triple + pyparsing_common.integer() + aa_triple

hgvs_protein_fs = Suppress('p.') + aa_triple + pyparsing_common.integer() + aa_triple + 'fs'

hgvs_genomic = Suppress('g.') + pyparsing_common.integer() + dna_nucleotide + Suppress('>') + dna_nucleotide

hgvs = (hgvs_rna_del | hgvs_dna_del | hgvs_chromosome | hgvs_snp | hgvs_protein_del |
        hgvs_protein_fs | hgvs_protein_mut | hgvs_genomic | '=' | '?')


class VariantParser(BaseParser):
    """
    http://www.hgvs.org/mutnomen/recs.html
    """
    def __init__(self):
        variant_tags = oneOf(['var', 'variant'])
        self.language = variant_tags + nest(hgvs)
        self.language.setParseAction(self.handle_variant)

    def handle_variant(self, s, l, tokens):
        tokens[0] = 'Variant'
        return tokens

    def get_language(self):
        return self.language



class PsubParser(BaseParser):
    def __init__(self):

        psub_tag = oneOf(['sub', 'substitution'])
        self.language = psub_tag + LP + amino_acid + WCW + pyparsing_common.integer() + WCW + amino_acid + RP
        self.language.setParseAction(self.handle_psub)

    def handle_psub(self, s, l, tokens):
        log.debug('PyBEL006 deprecated protein substitution function. User variant() instead. {}'.format(s))
        tokens[0] = 'Variant'
        return tokens

    def get_language(self):
        return self.language


class GsubParser(BaseParser):
    """
    This is a deprecated method from BEL 1.0 that had gene substitutions. Now, use the HGVS commands in
    Variant()
    """

    def __init__(self):

        gsub_tag = oneOf(['sub', 'substitution'])
        self.language = gsub_tag + nest(dna_nucleotide + WCW + pyparsing_common.integer() + WCW + dna_nucleotide)
        self.language.setParseAction(self.handle_gsub)

    def handle_gsub(self, s, l, tokens):
        log.debug('PyBEL009 old SNP annotation. Use variant() instead: {}'.format(s))
        tokens[0] = 'Variant'
        return tokens

    def get_language(self):
        return self.language


class FragmentParser(BaseParser):
    """
    2.2.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_proteolytic_fragments
    """

    def __init__(self):
        self.fragment_range = (pyparsing_common.integer() | '?') + Suppress('_') + (
            pyparsing_common.integer() | '?' | '*')
        fragment_tags = ['frag', 'fragment']
        fragment_1 = oneOf(fragment_tags) + LP + self.fragment_range + WCW + word + RP
        fragment_2 = oneOf(fragment_tags) + LP + self.fragment_range + RP
        fragment_3 = oneOf(fragment_tags) + LP + '?' + Optional(WCW + word) + RP

        self.language = fragment_3 | fragment_1 | fragment_2
        self.language.setParseAction(self.handle_fragment)

    def handle_fragment(self, s, l, tokens):
        tokens[0] = 'Fragment'
        return tokens

    def get_language(self):
        return self.language


class FusionParser(BaseParser):
    """
    2.6.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_fusion_fus
    """

    def __init__(self, namespace_parser=None):
        fusion_tags = ['fus', 'fusion']

        self.namespace_parser = namespace_parser if namespace_parser is not None else IdentifierParser()
        ns_val = self.namespace_parser.get_language()
        # sequence coordinates?
        range_coordinate = (Group(oneOf(['r', 'p']) + Suppress('.') + pyparsing_common.integer() +
                                  Suppress('_') + pyparsing_common.integer()) | '?')

        self.language = oneOf(fusion_tags) + LP + Group(ns_val) + WCW + range_coordinate + WCW + Group(
            ns_val) + WCW + range_coordinate + RP
        self.language.setParseAction(self.handle_fusion)

    def get_language(self):
        return self.language

    def handle_fusion(self, s, l, tokens):
        tokens[0] = 'Fusion'
        return tokens


class LocationParser(BaseParser):
    """
    2.2.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_cellular_location
    """

    def __init__(self, identifier_parser=None):
        """
        :param identifier_parser:
        :type identifier_parser: IdentifierParser
        :return:
        """
        self.identifier_parser = identifier_parser if identifier_parser is not None else IdentifierParser()
        identifier = self.identifier_parser.get_language()
        location_tags = ['loc', 'location']
        self.language = oneOf(location_tags) + LP + Group(identifier) + RP
        self.language.setParseAction(self.handle_location)

    def handle_location(self, s, l, tokens):
        tokens[0] = 'Location'
        return tokens

    def get_language(self):
        return self.language
