# -*- coding: utf-8 -*-

import logging

from pyparsing import Word, oneOf, replaceWith, Optional, Keyword, Suppress, Group, alphanums, MatchFirst
from pyparsing import pyparsing_common as ppc

from . import language
from .baseparser import BaseParser, WCW, word, nest, one_of_tags
from .language import amino_acid, dna_nucleotide, dna_nucleotide_labels, rna_nucleotide_labels
from .language import pmod_namespace, pmod_legacy_labels
from .parse_identifier import IdentifierParser
from ..constants import KIND, PMOD, GMOD, HGVS, PYBEL_DEFAULT_NAMESPACE, FRAGMENT, NAMESPACE, NAME, FUSION, LOCATION
from ..constants import PARTNER_3P, PARTNER_5P, RANGE_3P, RANGE_5P

log = logging.getLogger('pybel')

dna_nucleotide_seq = Word(''.join(dna_nucleotide_labels.keys()))
rna_nucleotide_seq = Word(''.join(rna_nucleotide_labels.keys()))


# Structural variants

class VariantParser(BaseParser):
    """
    The addition of a variant tag results in an entry called 'variants' in the data dictionary associated with a given
    node. This entry is a list with dictionaries describing each of the variants. All variants have the entry 'kind' to
    identify whether it is a PTM, gene modification, fragment, or HGVS variant. The 'kind' value for a variant
    is 'hgvs', but best descirbed by :code:`pybel.constants.HGVS`


    For example, the node :code:`p(HGNC:GSK3B, var(p.Gly123Arg))` is represented with the following:

    .. code::

        {
            'function': 'Protein',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'GSK3B'
            },
            'variants': [
                {
                    'kind': 'hgvs',
                    'identifier': 'p.Gly123Arg'
                }
            ]
        }


    .. seealso:: http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_variant_var
    .. seealso:: HVGS for conventions http://www.hgvs.org/mutnomen/recs.html
    """
    IDENTIFIER = 'identifier'

    def __init__(self):
        variant_tags = one_of_tags(tags=['var', 'variant'], canonical_tag=HGVS, identifier=KIND)
        variant_characters = Word(alphanums + '._*=?>')
        self.language = variant_tags + nest(variant_characters(self.IDENTIFIER))

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
        tokens[VariantParser.IDENTIFIER] = upgraded
        del tokens[self.REFERENCE]
        del tokens[self.POSITION]
        del tokens[self.VARIANT]
        return tokens

    def get_language(self):
        return self.language


class TruncParser(BaseParser):
    """
    Truncations in the legacy BEL 1.0 specification are automatically translated to BEL 2.0 with HGVS nomenclature.
    :code:`p(HGNC:AKT1, trunc(40))` becomes :code:`p(HGNC:AKT1, var(p.40*))` and is represented with the following
    dictionary:

    .. code::

        {
            'function': 'Protein',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'AKT1'
            },
            'variants': [
                {
                    'kind': 'hgvs',
                    'identifier': 'p.40*'
                }
            ]
        }


    Unfortunately, the HGVS nomenclature requires the encoding of the terminal amino acid which is exchanged
    for a stop codon, and this information is not required by BEL 1.0. For this example, the proper encoding
    of the truncation at position also includes the information that the 40th amino acid in the AKT1 is Cys. Its
    BEL encoding should be :code:`p(HGNC:AKT1, var(p.Cys40*))`. Temporary support has been added to
    compile these statements, but it's recommended they are upgraded by reexamining the supporting text, or
    looking up the amino acid sequence.
    """
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
        tokens[VariantParser.IDENTIFIER] = upgraded
        del tokens[self.POSITION]
        return tokens

    def get_language(self):
        return self.language


class GsubParser(BaseParser):
    """
    Gene substitutions are legacy statements defined in BEL 1.0. BEL 2.0 reccomends using HGVS strings. Luckily,
    the information contained in a BEL 1.0 encoding, such as :code:`g(HGNC:APP,sub(G,275341,C))` can be
    automatically translated to the appropriate HGVS :code:`g(HGNC:APP, var(c.275341G>C))`, assuming that all
    substitutions are using the reference coding gene sequence for numbering and not the genomic reference.
    The previous statements both produce the underlying data:

    .. code::

        {
            'function': 'Gene',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'APP'
            },
            'variants': [
                {
                    'kind': 'hgvs',
                    'identifier': 'c.275341G>C'
                }
            ]
        }
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
        upgraded = 'c.{}{}>{}'.format(tokens[self.POSITION], tokens[self.REFERENCE], tokens[self.VARIANT])
        log.debug('legacy sub() %s upgraded to %s', s, upgraded)
        tokens[VariantParser.IDENTIFIER] = upgraded
        del tokens[self.POSITION]
        del tokens[self.REFERENCE]
        del tokens[self.VARIANT]
        return tokens

    def get_language(self):
        return self.language


# Molecular modifications


class PmodParser(BaseParser):
    """
    The addition of a post-translational modification (PTM) tag results in an entry called 'variants'
    in the data dictionary associated with a given node. This entry is a list with dictionaries
    describing each of the variants. All variants have the entry 'kind' to identify whether it is
    a PTM, gene modification, fragment, or HGVS variant. The 'kind' value for PTM is 'pmod'.

    Each PMOD contains an identifier, which is a dictionary with the namespace and name, and can
    optionally include the position ('pos') and/or amino acid code ('code').

    For example, the node :code:`p(HGNC:GSK3B, pmod(P, S, 9))` is represented with the following:

    .. code::

        {
            'function': 'Protein',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'GSK3B'
            },
            'variants': [
                {
                    'kind': 'pmod',
                    'code': 'Ser',
                    'identifier': {
                        'name': 'Ph',
                        'namespace': 'PYBEL'
                    },
                    'pos': 9
                }
            ]
        }

    .. seealso:: http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_proteinmodification_pmod
    """

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
    The addition of a fragment results in an entry called 'variants'
    in the data dictionary associated with a given node. This entry is a list with dictionaries
    describing each of the variants. All variants have the entry 'kind' to identify whether it is
    a PTM, gene modification, fragment, or HGVS variant. The 'kind' value for a fragment is 'frag'.

    Each fragment contains an identifier, which is a dictionary with the namespace and name, and can
    optionally include the position ('pos') and/or amino acid code ('code').

    For example, the node :code:`p(HGNC:GSK3B, frag(45_129))` is represented with the following:

    .. code::

        {
            'function': 'Protein',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'GSK3B'
            },
            'variants': [
                {
                    'kind': 'frag',
                    'start': 45,
                    'stop': 129
                }
            ]
        }

    Additionally, nodes can have an asterick (*) or question mark (?) representing unbound
    or unknown fragments, respectively.

    A fragment may also be unknown, such as in the node :code:`p(HGNC:GSK3B, frag(?))`. This
    is represented with the key 'missing' and the value of '?' like:


    .. code::

        {
            'function': 'Protein',
            'identifier': {
                'namespace': 'HGNC',
                'name': 'GSK3B'
            },
            'variants': [
                {
                    'kind': 'frag',
                    'missing': '?',
                }
            ]
        }

    .. seealso:: 2.2.3 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_proteolytic_fragments
    """
    START = 'start'
    STOP = 'stop'
    MISSING = 'missing'
    DESCRIPTION = 'description'

    def __init__(self):
        self.fragment_range = (ppc.integer | '?')(self.START) + '_' + (ppc.integer | '?' | '*')(self.STOP)
        self.missing_fragment = Keyword('?')(self.MISSING)

        fragment_tag = one_of_tags(tags=['frag', 'fragment'], canonical_tag=FRAGMENT, identifier=KIND)

        self.language = fragment_tag + nest(
            (self.fragment_range | self.missing_fragment(self.MISSING)) + Optional(
                WCW + word(self.DESCRIPTION)))

    def get_language(self):
        return self.language


class GmodParser(BaseParser):
    """
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

    """
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
    return tokens[KIND], tokens[VariantParser.IDENTIFIER]


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
    Gene, RNA, protein, and miRNA fusions are all represented with the same underlying data structure. Below
    it is shown with uppercase letters referring to entries in :code:`pybel.constants` and
    :class:`pybel.parser.FusionParser`. For example, :code:`g(HGNC:BCR, fus(HGNC:JAK2, 1875, 2626))` is represented as:

    .. code::

        {
            FUNCTION: GENE,
            FUSION: {
                PARTNER_5P: {NAMESPACE: 'HGNC', NAME: 'BCR'},
                PARTNER_3P: {NAMESPACE: 'HGNC', NAME: 'JAK2'},
                RANGE_5P: {
                    FusionParser.REF: 'c',
                    FusionParser.LEFT: '?',
                    FusionParser.RIGHT: 1875

                },
                RANGE_3P: {
                    FusionParser.REF: 'c',
                    FusionParser.LEFT: 2626,
                    FusionParser.RIGHT: '?'
                }
            }
        }


    .. seealso:: 2.6.1 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_fusion_fus
    """

    REF = 'reference'
    LEFT = 'left'
    RIGHT = 'right'
    MISSING = 'missing'
    fusion_tags = oneOf(['fus', 'fusion']).setParseAction(replaceWith(FUSION))

    def __init__(self, namespace_parser=None):
        self.identifier_parser = namespace_parser if namespace_parser is not None else IdentifierParser()
        identifier = self.identifier_parser.get_language()
        # sequence coordinates?

        reference_seq = oneOf(['r', 'p', 'c'])
        coordinate = ppc.integer | '?'
        missing = Keyword('?')

        range_coordinate = missing(self.MISSING) | (
            reference_seq(self.REF) + Suppress('.') + coordinate(self.LEFT) + Suppress('_') + coordinate(self.RIGHT))

        self.language = self.fusion_tags + nest(Group(identifier)(PARTNER_5P), Group(range_coordinate)(RANGE_5P),
                                                Group(identifier)(PARTNER_3P), Group(range_coordinate)(RANGE_3P))

    def get_language(self):
        return self.language


class LocationParser(BaseParser):
    """Parses loc() elements
    .. seealso:: 2.2.4 http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_cellular_location
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
        self.language = Group(location_tag + nest(identifier))(LOCATION)

    def get_language(self):
        return self.language
