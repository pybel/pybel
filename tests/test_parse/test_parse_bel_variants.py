# -*- coding: utf-8 -*-

"""Test parsing variants."""

import logging
import unittest

from pybel.constants import (
    BEL_DEFAULT_NAMESPACE, FRAGMENT, FRAGMENT_DESCRIPTION, FRAGMENT_MISSING, FRAGMENT_START, FRAGMENT_STOP,
    FUSION_MISSING, FUSION_REFERENCE, FUSION_START, FUSION_STOP, GMOD, IDENTIFIER, KIND, LOCATION, NAME, NAMESPACE,
    PARTNER_3P, PARTNER_5P, PMOD, PMOD_CODE, PMOD_POSITION, RANGE_3P, RANGE_5P,
)
from pybel.dsl import gmod, hgvs, pmod
from pybel.language import Entity
from pybel.parser.modifiers import (
    get_fragment_language, get_fusion_language, get_gene_modification_language, get_gene_substitution_language,
    get_hgvs_language, get_location_language, get_protein_modification_language, get_protein_substitution_language,
    get_truncation_language,
)
from pybel.parser.parse_identifier import IdentifierParser

log = logging.getLogger(__name__)


class TestHGVSParser(unittest.TestCase):
    def setUp(self):
        self.parser = get_hgvs_language()

    def test_protein_del(self):
        statement = 'variant(p.Phe508del)'
        expected = hgvs('p.Phe508del')
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asDict())

    def test_protein_del_quoted(self):
        statement = 'variant("p.Phe508del")'
        expected = hgvs('p.Phe508del')
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asDict())

    def test_protein_mut(self):
        statement = 'var(p.Gly576Ala)'
        expected = hgvs('p.Gly576Ala')
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asDict())

    def test_unspecified(self):
        statement = 'var(=)'
        expected = hgvs('=')
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asDict())

    def test_frameshift(self):
        statement = 'variant(p.Thr1220Lysfs)'
        expected = hgvs('p.Thr1220Lysfs')
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asDict())

    def test_snp(self):
        statement = 'var(c.1521_1523delCTT)'
        expected = hgvs('c.1521_1523delCTT')
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asDict())

    def test_chromosome_1(self):
        statement = 'variant(g.117199646_117199648delCTT)'
        expected = hgvs('g.117199646_117199648delCTT')
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asDict())

    def test_chromosome_2(self):
        statement = 'var(c.1521_1523delCTT)'
        expected = hgvs('c.1521_1523delCTT')
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asDict())

    def test_rna_del(self):
        statement = 'var(r.1653_1655delcuu)'
        expected = hgvs('r.1653_1655delcuu')
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asDict())

    def test_protein_trunc_triple(self):
        statement = 'var(p.Cys65*)'
        result = self.parser.parseString(statement)
        expected = hgvs('p.Cys65*')
        self.assertEqual(expected, result.asDict())

    def test_protein_trunc_legacy(self):
        statement = 'var(p.65*)'
        result = self.parser.parseString(statement)
        expected = hgvs('p.65*')
        self.assertEqual(expected, result.asDict())


class TestPmod(unittest.TestCase):
    def setUp(self):
        identifier_parser = IdentifierParser()
        identifier_qualified = identifier_parser.identifier_qualified
        self.parser = get_protein_modification_language(identifier_qualified)

    def _help_test_pmod_simple(self, statement):
        result = self.parser.parseString(statement)

        expected = {
            KIND: PMOD,
            IDENTIFIER: {
                NAMESPACE: BEL_DEFAULT_NAMESPACE,
                NAME: 'Ph',
            },
        }
        self.assertEqual(expected, pmod('Ph'))
        self.assertEqual(expected, result.asDict())

    def test_bel_name(self):
        # long function, legacy modification
        self._help_test_pmod_simple('proteinModification(P)')
        # long function, new modification
        self._help_test_pmod_simple('proteinModification(Ph)')
        # long function, qualified modification
        self._help_test_pmod_simple('proteinModification(bel:Ph)')

        # short function, legacy modification
        self._help_test_pmod_simple('pmod(P)')
        # short function, new modification
        self._help_test_pmod_simple('pmod(Ph)')
        # short function, qualified modification
        self._help_test_pmod_simple('pmod(bel:Ph)')

    def _help_test_pmod_with_residue(self, statement):
        result = self.parser.parseString(statement)

        expected = {
            KIND: PMOD,
            IDENTIFIER: {
                NAMESPACE: BEL_DEFAULT_NAMESPACE,
                NAME: 'Ph',
            },
            PMOD_CODE: 'Ser',
        }
        self.assertEqual(expected, pmod('Ph', code='Ser'))
        self.assertEqual(expected, result.asDict())

    def test_residue(self):
        # short amino acid
        self._help_test_pmod_with_residue('pmod(Ph, S)')
        # long amino acid
        self._help_test_pmod_with_residue('pmod(Ph, Ser)')

    def _help_test_pmod_full(self, statement):
        result = self.parser.parseString(statement)

        expected = {
            KIND: PMOD,
            IDENTIFIER: {
                NAMESPACE: BEL_DEFAULT_NAMESPACE,
                NAME: 'Ph',
            },
            PMOD_CODE: 'Ser',
            PMOD_POSITION: 473
        }

        self.assertEqual(expected, pmod('Ph', code='Ser', position=473))
        self.assertEqual(expected, result.asDict())

    def test_full(self):
        self._help_test_pmod_full('proteinModification(P, Ser, 473)')
        self._help_test_pmod_full('proteinModification(P, S, 473)')
        self._help_test_pmod_full('proteinModification(Ph, Ser, 473)')
        self._help_test_pmod_full('proteinModification(Ph, S, 473)')
        self._help_test_pmod_full('proteinModification(bel:Ph, Ser, 473)')
        self._help_test_pmod_full('proteinModification(bel:Ph, S, 473)')
        self._help_test_pmod_full('pmod(P, Ser, 473)')
        self._help_test_pmod_full('pmod(P, S, 473)')
        self._help_test_pmod_full('pmod(Ph, Ser, 473)')
        self._help_test_pmod_full('pmod(Ph, S, 473)')
        self._help_test_pmod_full('pmod(bel:Ph, Ser, 473)')
        self._help_test_pmod_full('pmod(bel:Ph, S, 473)')

    def _help_test_non_standard_namespace(self, statement):
        result = self.parser.parseString(statement)

        expected = {
            KIND: PMOD,
            IDENTIFIER: Entity('MOD', 'PhosRes'),
            PMOD_CODE: 'Ser',
            PMOD_POSITION: 473
        }

        self.assertEqual(expected, pmod(name='PhosRes', namespace='MOD', code='Ser', position=473))
        self.assertEqual(expected, result.asDict())

    def test_full_with_non_standard_namespace(self):
        self._help_test_non_standard_namespace('proteinModification(MOD:PhosRes, S, 473)')
        self._help_test_non_standard_namespace('proteinModification(MOD:PhosRes, Ser, 473)')
        self._help_test_non_standard_namespace('pmod(MOD:PhosRes, S, 473)')
        self._help_test_non_standard_namespace('pmod(MOD:PhosRes, Ser, 473)')


class TestGeneModification(unittest.TestCase):
    def setUp(self):
        identifier_parser = IdentifierParser()
        identifier_qualified = identifier_parser.identifier_qualified
        self.parser = get_gene_modification_language(identifier_qualified)

        self.expected = gmod('Me')

    def test_dsl(self):
        self.assertEqual({
            KIND: GMOD,
            IDENTIFIER: {
                NAME: 'Me',
                NAMESPACE: BEL_DEFAULT_NAMESPACE
            }
        }, self.expected)

    def test_gmod_short(self):
        statement = 'gmod(M)'
        result = self.parser.parseString(statement)
        self.assertEqual(self.expected, result.asDict())

    def test_gmod_unabbreviated(self):
        statement = 'gmod(Me)'
        result = self.parser.parseString(statement)
        self.assertEqual(self.expected, result.asDict())

    def test_gmod_long(self):
        statement = 'geneModification(methylation)'
        result = self.parser.parseString(statement)
        self.assertEqual(self.expected, result.asDict())


class TestProteinSubstitution(unittest.TestCase):
    def setUp(self):
        self.parser = get_protein_substitution_language()

    def test_psub_1(self):
        statement = 'sub(A, 127, Y)'
        result = self.parser.parseString(statement)

        expected_list = hgvs('p.Ala127Tyr')
        self.assertEqual(expected_list, result.asDict())

    def test_psub_2(self):
        statement = 'sub(Ala, 127, Tyr)'
        result = self.parser.parseString(statement)

        expected_list = hgvs('p.Ala127Tyr')
        self.assertEqual(expected_list, result.asDict())


class TestGeneSubstitutionParser(unittest.TestCase):
    def setUp(self):
        self.parser = get_gene_substitution_language()

    def test_gsub(self):
        statement = 'sub(G,308,A)'
        result = self.parser.parseString(statement)

        expected_dict = hgvs('c.308G>A')
        self.assertEqual(expected_dict, result.asDict())


class TestFragmentParser(unittest.TestCase):
    """See http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_examples_2"""

    def setUp(self):
        self.parser = get_fragment_language()

    def help_test_known_length(self, s):
        result = self.parser.parseString(s)
        expected = {
            KIND: FRAGMENT,
            FRAGMENT_START: 5,
            FRAGMENT_STOP: 20
        }
        self.assertEqual(expected, result.asDict())

    def test_known_length_unquoted(self):
        """test known length"""
        s = 'frag(5_20)'
        self.help_test_known_length(s)

    def test_known_length_quotes(self):
        """test known length"""
        s = 'frag("5_20")'
        self.help_test_known_length(s)

    def help_test_unknown_length(self, s):
        result = self.parser.parseString(s)
        expected = {
            KIND: FRAGMENT,
            FRAGMENT_START: 1,
            FRAGMENT_STOP: '?'
        }
        self.assertEqual(expected, result.asDict())

    def test_unknown_length_unquoted(self):
        """amino-terminal fragment of unknown length"""
        s = 'frag(1_?)'
        self.help_test_unknown_length(s)

    def test_unknown_length_quoted(self):
        """amino-terminal fragment of unknown length"""
        s = 'frag("1_?")'
        self.help_test_unknown_length(s)

    def help_test_unknown_start_stop(self, s):
        result = self.parser.parseString(s)
        expected = {
            KIND: FRAGMENT,
            FRAGMENT_START: '?',
            FRAGMENT_STOP: '*'
        }
        self.assertEqual(expected, result.asDict())

    def test_unknown_start_stop_unquoted(self):
        """fragment with unknown start/stop"""
        s = 'frag(?_*)'
        self.help_test_unknown_start_stop(s)

    def test_unknown_start_stop_quoted(self):
        """fragment with unknown start/stop"""
        s = 'frag("?_*")'
        self.help_test_unknown_start_stop(s)

    def help_test_descriptor(self, s):
        result = self.parser.parseString(s)
        expected = {
            KIND: FRAGMENT,
            FRAGMENT_MISSING: '?',
            FRAGMENT_DESCRIPTION: '55kD'
        }
        self.assertEqual(expected, result.asDict())

    def test_descriptor_unquoted(self):
        """fragment with unknown start/stop and a descriptor"""
        s = 'frag(?, "55kD")'
        self.help_test_descriptor(s)

    def test_descriptor_quoted(self):
        """fragment with unknown start/stop and a descriptor"""
        s = 'frag("?", "55kD")'
        self.help_test_descriptor(s)


class TestTruncationParser(unittest.TestCase):
    def setUp(self):
        self.parser = get_truncation_language()

    def test_trunc_1(self):
        statement = 'trunc(40)'
        result = self.parser.parseString(statement)

        expected = hgvs('p.40*')
        self.assertEqual(expected, result.asDict())

    def test_trunc_2(self):
        """Test a truncation in which the amino acid is specified."""
        statement = 'trunc(Gly40)'
        result = self.parser.parseString(statement)

        expected = hgvs('p.Gly40*')
        self.assertEqual(expected, result.asDict())

    def test_trunc_missing_number(self):
        """Test that an error is raised for a truncation in which the position is omitted."""
        statement = 'trunc(Gly)'
        with self.assertRaises(Exception):
            result = self.parser.parseString(statement)


class TestFusionParser(unittest.TestCase):
    def setUp(self):
        identifier_parser = IdentifierParser()
        identifier_qualified = identifier_parser.identifier_qualified
        self.parser = get_fusion_language(identifier_qualified)

    def test_rna_fusion_known_breakpoints(self):
        """RNA abundance of fusion with known breakpoints"""
        statement = 'fus(HGNC:TMPRSS2, r.1_79, HGNC:ERG, r.312_5034)'
        result = self.parser.parseString(statement)

        expected = {
            PARTNER_5P: {
                NAMESPACE: 'HGNC',
                NAME: 'TMPRSS2'
            },
            RANGE_5P: {
                FUSION_REFERENCE: 'r',
                FUSION_START: 1,
                FUSION_STOP: 79

            },
            PARTNER_3P: {
                NAMESPACE: 'HGNC',
                NAME: 'ERG'
            },
            RANGE_3P: {
                FUSION_REFERENCE: 'r',
                FUSION_START: 312,
                FUSION_STOP: 5034
            }
        }

        self.assertEqual(expected, result.asDict())

    def test_rna_fusion_unspecified_breakpoints(self):
        """RNA abundance of fusion with unspecified breakpoints"""
        statement = 'fus(HGNC:TMPRSS2, ?, HGNC:ERG, ?)'
        result = self.parser.parseString(statement)

        expected = {
            PARTNER_5P: {
                NAMESPACE: 'HGNC',
                NAME: 'TMPRSS2'
            },
            RANGE_5P: {
                FUSION_MISSING: '?'

            },
            PARTNER_3P: {
                NAMESPACE: 'HGNC',
                NAME: 'ERG'
            },
            RANGE_3P: {
                FUSION_MISSING: '?'
            }
        }

        self.assertEqual(expected, result.asDict())

    def test_rna_fusion_specified_one_fuzzy_breakpoint(self):
        """RNA abundance of fusion with unspecified breakpoints"""
        statement = 'fusion(HGNC:TMPRSS2, r.1_79, HGNC:ERG, r.?_1)'
        result = self.parser.parseString(statement)

        expected = {
            PARTNER_5P: {
                NAMESPACE: 'HGNC',
                NAME: 'TMPRSS2'
            },
            RANGE_5P: {
                FUSION_REFERENCE: 'r',
                FUSION_START: 1,
                FUSION_STOP: 79

            },
            PARTNER_3P: {
                NAMESPACE: 'HGNC',
                NAME: 'ERG'
            },
            RANGE_3P: {
                FUSION_REFERENCE: 'r',
                FUSION_START: '?',
                FUSION_STOP: 1
            }
        }

        self.assertEqual(expected, result.asDict())

    def test_rna_fusion_specified_fuzzy_breakpoints(self):
        """RNA abundance of fusion with unspecified breakpoints"""
        statement = 'fusion(HGNC:TMPRSS2, r.1_?, HGNC:ERG, r.?_1)'
        result = self.parser.parseString(statement)

        expected = {
            PARTNER_5P: {
                NAMESPACE: 'HGNC',
                NAME: 'TMPRSS2'
            },
            RANGE_5P: {
                FUSION_REFERENCE: 'r',
                FUSION_START: 1,
                FUSION_STOP: '?'

            },
            PARTNER_3P: {
                NAMESPACE: 'HGNC',
                NAME: 'ERG'
            },
            RANGE_3P: {
                FUSION_REFERENCE: 'r',
                FUSION_START: '?',
                FUSION_STOP: 1
            }
        }

        self.assertEqual(expected, result.asDict())


class TestLocation(unittest.TestCase):
    def setUp(self):
        identifier_parser = IdentifierParser()
        identifier_qualified = identifier_parser.identifier_qualified
        self.parser = get_location_language(identifier_qualified)

    def test_a(self):
        statement = 'loc(GO:intracellular)'
        result = self.parser.parseString(statement)
        expected = {
            LOCATION: {NAMESPACE: 'GO', NAME: 'intracellular'}
        }
        self.assertEqual(expected, result.asDict())
