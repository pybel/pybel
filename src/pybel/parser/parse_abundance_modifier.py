# -*- coding: utf-8 -*-

import logging

from pyparsing import Word, oneOf, replaceWith, Optional, Keyword, Suppress, Group, alphanums, MatchFirst
from pyparsing import pyparsing_common as ppc

from . import language
from .baseparser import BaseParser, WCW, word, nest, one_of_tags
from .language import amino_acid, dna_nucleotide, dna_nucleotide_labels, rna_nucleotide_labels
from .language import pmod_namespace, pmod_legacy_labels
from .parse_identifier import IdentifierParser
from ..constants import KIND, PMOD, GMOD, HGVS, PYBEL_DEFAULT_NAMESPACE, FRAGMENT, NAMESPACE, NAME

log = logging.getLogger('pybel')

dna_nucleotide_seq = Word(''.join(dna_nucleotide_labels.keys()))
rna_nucleotide_seq = Word(''.join(rna_nucleotide_labels.keys()))


def build_variant_dict(variant):
    return {KIND: HGVS, HGVS: variant}


# Structural variants

class VariantParser(BaseParser):
    """Parsers variants

    See HVGS for conventions http://www.hgvs.org/mutnomen/recs.html
    """

    def __init__(self):
        variant_tags = one_of_tags(tags=['var', 'variant'], canonical_tag=HGVS, identifier=KIND)
        variant_characters = Word(alphanums + '._*=?>')
        self.language = variant_tags + nest(variant_characters.setResultsName(HGVS))

    def get_language(self):
        return self.language


class PsubParser(BaseParser):
    REFERENCE = 'reference'
    POSITION = 'position'
    VARIANT = 'variant'

    def __init__(self):
        psub_tag = one_of_tags(tags=['sub', 'substitution'], canonical_tag=HGVS, identifier=KIND)
        self.language = psub_tag + nest(amino_acid(self.REFERENCE),
                                        ppc.integer(self.POSITION),
                                        amino_acid(self.VARIANT))
        self.language.setParseAction(self.handle_psub)

    def handle_psub(self, s, l, tokens):
        upgraded = 'p.{}{}{}'.format(tokens[self.REFERENCE], tokens[self.POSITION], tokens[self.VARIANT])
        log.log(5, 'sub() in p() is deprecated: %s. Upgraded to %s', s, upgraded)
        tokens[HGVS] = upgraded
        del tokens[self.REFERENCE]
        del tokens[self.POSITION]
        del tokens[self.VARIANT]
        return tokens

    def get_language(self):
        return self.language


class TruncParser(BaseParser):
    POSITION = 'position'

    def __init__(self):
        trunc_tag = one_of_tags(tags=['trunc', 'truncation'], canonical_tag=HGVS, identifier=KIND)
        self.language = trunc_tag + nest(ppc.integer(self.POSITION))
        self.language.setParseAction(self.handle_trunc_legacy)

    # FIXME this isn't correct HGVS nomenclature, but truncation isn't forward compatible without more information
    def handle_trunc_legacy(self, s, l, tokens):
        upgraded = 'p.{}*'.format(tokens[self.POSITION])
        log.warning(
            'trunc() is deprecated. Please look up reference terminal amino acid and encode with HGVS: {}'.format(s))
        tokens[HGVS] = upgraded
        del tokens[self.POSITION]
        return tokens

    def get_language(self):
        return self.language


class GsubParser(BaseParser):
    """
    This is a deprecated method from BEL 1.0 that had gene substitutions. Now, use the HGVS commands in
    Variant()
    """

    REFERENCE = 'reference'
    POSITION = 'position'
    VARIANT = 'variant'

    def __init__(self):
        gsub_tag = one_of_tags(tags=['sub', 'substitution'], canonical_tag=HGVS, identifier=KIND)
        self.language = gsub_tag + nest(dna_nucleotide(self.REFERENCE), ppc.integer(self.POSITION),
                                        dna_nucleotide(self.VARIANT))
        self.language.setParseAction(self.handle_gsub)

    def handle_gsub(self, s, l, tokens):
        upgraded = 'g.{}{}>{}'.format(tokens[self.POSITION], tokens[self.REFERENCE], tokens[self.VARIANT])
        log.debug('legacy sub() %s upgraded to %s', s, upgraded)
        tokens[HGVS] = upgraded
        del tokens[self.POSITION]
        del tokens[self.REFERENCE]
        del tokens[self.VARIANT]
        return tokens

    def get_language(self):
        return self.language


# Molecular modifications


class PmodParser(BaseParser):
    IDENTIFIER = 'identifier'
    CODE = 'code'
    POSITION = 'pos'
    ORDER = [KIND, IDENTIFIER, CODE, POSITION]

    def __init__(self, namespace_parser=None):
        """

        :param namespace_parser:
        :type namespace_parser: IdentifierParser
        :return:
        """

        self.namespace_parser = namespace_parser if namespace_parser is not None else IdentifierParser()

        pmod_tag = one_of_tags(tags=['pmod', 'proteinModification'], canonical_tag=PMOD, identifier=KIND)

        pmod_default_ns = oneOf(pmod_namespace.keys()).setParseAction(self.handle_pmod_default_ns)
        pmod_legacy_ns = oneOf(pmod_legacy_labels.keys()).setParseAction(self.handle_pmod_legacy_ns)

        pmod_identifier = MatchFirst([
            Group(self.namespace_parser.identifier_qualified),
            Group(pmod_default_ns),
            Group(pmod_legacy_ns)
        ])

        self.language = pmod_tag + nest(pmod_identifier(self.IDENTIFIER) +
                                        Optional(
                                            WCW + amino_acid(self.CODE) + Optional(WCW + ppc.integer(self.POSITION))))

    def handle_pmod_default_ns(self, s, l, tokens):
        tokens[NAMESPACE] = PYBEL_DEFAULT_NAMESPACE
        tokens['name'] = language.pmod_namespace[tokens[0]]
        return tokens

    def handle_pmod_legacy_ns(self, s, l, tokens):
        upgraded = language.pmod_legacy_labels[tokens[0]]
        log.debug('legacy pmod() value %s upgraded to %s', s, upgraded)
        tokens['namespace'] = PYBEL_DEFAULT_NAMESPACE
        tokens['name'] = upgraded
        return tokens

    def get_language(self):
        return self.language


class FragmentParser(BaseParser):
    """
    2.2.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_proteolytic_fragments
    """
    START = 'start'
    STOP = 'stop'
    MISSING = 'missing'
    DESCRIPTION = 'description'

    def __init__(self):
        self.fragment_range = (ppc.integer | '?')(self.START) + '_' + (ppc.integer | '?' | '*')(self.STOP)
        self.missing_fragment = Keyword('?')(self.MISSING)

        # fragment_tag = oneOf(['frag', 'fragment']).setParseAction(replaceWith('Fragment'))
        fragment_tag = one_of_tags(tags=['frag', 'fragment'], canonical_tag=FRAGMENT, identifier=KIND)

        self.language = fragment_tag + nest(
            (self.fragment_range | self.missing_fragment(self.MISSING)) + Optional(
                WCW + word(self.DESCRIPTION)))

    def get_language(self):
        return self.language


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


def canonicalize_hgvs(tokens):
    return tokens[KIND], tokens[HGVS]


def canonicalize_pmod(tokens):
    return (PMOD, (tokens[PmodParser.IDENTIFIER][NAMESPACE], tokens[PmodParser.IDENTIFIER][NAME])) + tuple(
        tokens[key] for key in PmodParser.ORDER[2:] if key in tokens)


def canonicalize_gmod(tokens):
    return (GMOD, (tokens[GmodParser.IDENTIFIER][NAMESPACE], tokens[GmodParser.IDENTIFIER][NAME])) + tuple(
        tokens[key] for key in GmodParser.ORDER[2:] if key in tokens)


def canonicalize_frag(tokens):
    if FragmentParser.MISSING in tokens:
        result = FRAGMENT, '?'
    else:
        result = FRAGMENT, (tokens[FragmentParser.START], tokens[FragmentParser.STOP])

    if FragmentParser.DESCRIPTION in tokens:
        return result + (tokens[FragmentParser.DESCRIPTION],)

    return result


def canonicalize_variant(tokens):
    if tokens[KIND] == HGVS:
        return canonicalize_hgvs(tokens)
    elif tokens[KIND] == PMOD:
        return canonicalize_pmod(tokens)
    elif tokens[KIND] == GMOD:
        return canonicalize_gmod(tokens)
    elif tokens[KIND] == FRAGMENT:
        return canonicalize_frag(tokens)


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
