# -*- coding: utf-8 -*-

import logging

from pyparsing import Word, Literal, oneOf, replaceWith, Optional, Keyword, MatchFirst, Suppress, Group
from pyparsing import pyparsing_common as ppc

from .baseparser import BaseParser, WCW, word, nest
from .language import aa_triple, amino_acid, dna_nucleotide, dna_nucleotide_labels, rna_nucleotide_labels
from .parse_identifier import IdentifierParser

log = logging.getLogger('pybel')

dna_nucleotide_seq = Word(''.join(dna_nucleotide_labels.keys()))
rna_nucleotide_seq = Word(''.join(rna_nucleotide_labels.keys()))

"""
From http://varnomen.hgvs.org/recommendations/general/
a letter prefix should be used to indicate the reference sequence used. Accepted prefixes are;
“g.” for a genomic reference sequence
“m.” for a mitochondrial reference sequence
“c.” for a coding DNA reference sequence
“n.” for a non-coding DNA reference sequence
“r.” for an RNA reference sequence (transcript)
“p.” for a protein reference sequence
"""

p_dot = Literal('p.')  #: protein reference sequence
r_dot = Literal('r.')  #: rna transcript reference sequence
c_dot = Literal('c.')  #: coding DNA reference sequence
g_dot = Literal('g.')  #: genomic reference sequence

deletion = Literal('del')

hgvs_rna_del = (r_dot + ppc.integer + '_' + ppc.integer + 'del' + rna_nucleotide_seq)

hgvs_dna_del = (c_dot + ppc.integer + '_' + ppc.integer + 'del' + dna_nucleotide_seq)

hgvs_chromosome = (g_dot + ppc.integer + '_' + ppc.integer + 'del' + dna_nucleotide_seq)

hgvs_snp = 'del' + dna_nucleotide_seq

hgvs_protein_del = p_dot + aa_triple + ppc.integer + 'del'

hgvs_protein_mut = p_dot + aa_triple + ppc.integer + aa_triple

hgvs_protein_fs = p_dot + aa_triple + ppc.integer + aa_triple + 'fs'

hgvs_genomic = g_dot + ppc.integer + dna_nucleotide + '>' + dna_nucleotide

hgvs_protein_truncation = p_dot + Optional(amino_acid) + ppc.integer('location') + '*'

hgvs = MatchFirst([hgvs_protein_truncation, hgvs_rna_del, hgvs_dna_del, hgvs_chromosome, hgvs_snp, hgvs_protein_del,
                   hgvs_protein_fs, hgvs_protein_mut, hgvs_genomic, Keyword('='), Keyword('?')])


class VariantParser(BaseParser):
    """
    http://www.hgvs.org/mutnomen/recs.html
    """

    def __init__(self):
        variant_tags = oneOf(['var', 'variant']).setParseAction(replaceWith('Variant'))
        self.language = variant_tags + nest(hgvs)

    def get_language(self):
        return self.language


class PsubParser(BaseParser):
    def __init__(self):
        psub_tag = oneOf(['sub', 'substitution']).setParseAction(replaceWith('Variant'))
        self.language = psub_tag + nest(amino_acid('reference'), ppc.integer('position'), amino_acid('variant'))
        self.language.setParseAction(self.handle_psub)

    def handle_psub(self, s, l, tokens):
        log.log(5, 'PyBEL006 sub() is deprecated: %s', s)
        return ['Variant', 'p.', tokens['reference'], tokens['position'], tokens['variant']]

    def get_language(self):
        return self.language


class TruncParser(BaseParser):
    def __init__(self):
        trunc_tag = oneOf(['trunc', 'truncation']).setParseAction(replaceWith('Variant'))
        self.language = trunc_tag + nest(ppc.integer('position'))
        self.language.setParseAction(self.handle_trunc_legacy)

    # FIXME this isn't correct HGVS nomenclature, but truncation isn't forward compatible without more information
    def handle_trunc_legacy(self, s, l, tokens):
        log.log(5, 'PyBEL025 trunc() is deprecated. Please look up reference terminal amino acid: {}'.format(s))
        return ['Variant', 'p.', tokens['position'], '*']

    def get_language(self):
        return self.language


class GsubParser(BaseParser):
    """
    This is a deprecated method from BEL 1.0 that had gene substitutions. Now, use the HGVS commands in
    Variant()
    """

    def __init__(self):
        gsub_tag = oneOf(['sub', 'substitution']).setParseAction(replaceWith('Variant'))
        self.language = gsub_tag + nest(dna_nucleotide('reference'), ppc.integer('position'),
                                        dna_nucleotide('variant'))
        self.language.setParseAction(self.handle_gsub)

    def handle_gsub(self, s, l, tokens):
        log.log(5, 'PyBEL009 sub() is deprecated: %s', s)
        return ['Variant', 'g.', tokens['position'], tokens['reference'], '>', tokens['variant']]

    def get_language(self):
        return self.language


class FragmentParser(BaseParser):
    """
    2.2.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_proteolytic_fragments
    """

    def __init__(self):
        self.fragment_range = (ppc.integer | '?')('start') + '_' + (ppc.integer | '?' | '*')('stop')
        self.missing_fragment = Keyword('?')('missing')
        fragment_tag = oneOf(['frag', 'fragment']).setParseAction(replaceWith('Fragment'))
        self.language = fragment_tag + nest(
            (self.fragment_range | self.missing_fragment) + Optional(WCW + word('description')))

    def get_language(self):
        return self.language


class FusionParser(BaseParser):
    """
    2.6.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_fusion_fus
    """

    def __init__(self, namespace_parser=None):
        fusion_tags = oneOf(['fus', 'fusion']).setParseAction(replaceWith('Fusion'))

        self.identifier_parser = namespace_parser if namespace_parser is not None else IdentifierParser()
        identifier = self.identifier_parser.get_language()
        # sequence coordinates?
        range_coordinate = (Group(oneOf(['r', 'p', 'c']) + Suppress('.') + ppc.integer +
                                  Suppress('_') + ppc.integer) | '?')

        self.language = fusion_tags + nest(Group(identifier)('partner_5p'), range_coordinate('range_5p'),
                                           Group(identifier)('partner_3p'), range_coordinate('range_3p'))

    def get_language(self):
        return self.language


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
        location_tag = Suppress(oneOf(['loc', 'location']))
        self.language = Group(location_tag + nest(identifier))('location')

    def get_language(self):
        return self.language
