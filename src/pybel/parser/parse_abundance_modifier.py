# -*- coding: utf-8 -*-

import logging

from pyparsing import Word, oneOf, replaceWith, Optional, Keyword, Suppress, Group, alphanums
from pyparsing import pyparsing_common as ppc

from pybel.parser.language import pmod_namespace, pmod_legacy_labels
from . import language
from .baseparser import BaseParser, WCW, word, nest
from .language import amino_acid, dna_nucleotide, dna_nucleotide_labels, rna_nucleotide_labels
from .parse_identifier import IdentifierParser

log = logging.getLogger('pybel')

dna_nucleotide_seq = Word(''.join(dna_nucleotide_labels.keys()))
rna_nucleotide_seq = Word(''.join(rna_nucleotide_labels.keys()))


class VariantParser(BaseParser):
    """Parsers variants

    See HVGS for conventions http://www.hgvs.org/mutnomen/recs.html
    """

    def __init__(self):
        variant_tags = oneOf(['var', 'variant']).setParseAction(replaceWith('Variant'))
        variant_characters = Word(alphanums + '._*=?>')
        self.language = variant_tags + nest(variant_characters)

    def get_language(self):
        return self.language


class PsubParser(BaseParser):
    def __init__(self):
        psub_tag = oneOf(['sub', 'substitution']).setParseAction(replaceWith('Variant'))
        self.language = psub_tag + nest(amino_acid('reference'), ppc.integer('position'), amino_acid('variant'))
        self.language.setParseAction(self.handle_psub)

    def handle_psub(self, s, l, tokens):
        upgraded = 'p.{}{}{}'.format(tokens['reference'], tokens['position'], tokens['variant'])
        log.log(5, 'sub() in p() is deprecated: %s. Upgraded to %s', s, upgraded)
        return ['Variant', upgraded]

    def get_language(self):
        return self.language


class TruncParser(BaseParser):
    def __init__(self):
        trunc_tag = oneOf(['trunc', 'truncation']).setParseAction(replaceWith('Variant'))
        self.language = trunc_tag + nest(ppc.integer('position'))
        self.language.setParseAction(self.handle_trunc_legacy)

    # FIXME this isn't correct HGVS nomenclature, but truncation isn't forward compatible without more information
    def handle_trunc_legacy(self, s, l, tokens):
        upgraded = 'p.{}*'.format(tokens['position'])
        log.warning('trunc() is deprecated. Please look up reference terminal amino acid, and encode with HGVS: {}'.format(s))
        return ['Variant', upgraded]

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
        upgraded = 'g.{}{}{}{}'.format(tokens['position'], tokens['reference'], '>', tokens['variant'])
        log.warning('sub() in g() is deprecated: %s. Upgraded to %s', s, upgraded)
        return ['Variant', upgraded]

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

        pmod_1 = pmod_tag + nest(pmod_identifier('identifier'), amino_acid('code'), ppc.integer('pos'))
        pmod_2 = pmod_tag + nest(pmod_identifier('identifier'), amino_acid('code'))
        pmod_3 = pmod_tag + nest(pmod_identifier('identifier'))

        self.language = pmod_1 | pmod_2 | pmod_3
        self.language.setParseAction(self.handle_protein_modification)

    def handle_protein_modification(self, s, l, tokens):
        return tokens

    def handle_pmod_default_ns(self, s, l, tokens):
        return [language.pmod_namespace[tokens[0]]]

    def handle_pmod_legacy_ns(self, s, l, tokens):
        upgraded = language.pmod_legacy_labels[tokens[0]]
        log.log(5, 'PyBEL016 legacy pmod() values: %s. Upgraded to %s.', s, upgraded)
        return [upgraded]

    def get_language(self):
        return self.language


class GmodParser(BaseParser):
    def __init__(self, namespace_parser=None):
        """

        :param namespace_parser:
        :type namespace_parser: IdentifierParser
        :return:
        """

        self.namespace_parser = namespace_parser if namespace_parser is not None else IdentifierParser()

        gmod_tag = oneOf(['gmod', 'geneModification'])
        gmod_tag.addParseAction(replaceWith('GeneModification'))

        gmod_default_ns = oneOf(language.gmod_namespace.keys()).setParseAction(self.handle_gmod)

        gmod_identifier = Group(self.namespace_parser.identifier_qualified) | gmod_default_ns

        # pmod_1 = gmod_tag + nest(pmod_identifier('identifier'), amino_acid('code'), ppc.integer('pos'))
        gmod_1 = gmod_tag + nest(gmod_identifier)

        self.language = gmod_1

    def handle_gmod(self, s, l, tokens):
        return [language.gmod_namespace[tokens[0]]]

    def get_language(self):
        return self.language
