import logging
import unittest

from pybel.parser.parse_abundance_modifier import PmodParser, GmodParser, PsubParser, GsubParser, TruncParser, \
    FusionParser, LocationParser, FragmentParser
from pybel.parser.parse_abundance_modifier import VariantParser

log = logging.getLogger(__name__)


class TestVariantParser(unittest.TestCase):
    def setUp(self):
        self.parser = VariantParser()

    def test_protein_del(self):
        statement = 'variant(p.Phe508del)'
        expected = ['Variant', 'p.Phe508del']
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_protein_mut(self):
        statement = 'var(p.Gly576Ala)'
        expected = ['Variant', 'p.Gly576Ala']
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_unspecified(self):
        statement = 'var(=)'
        expected = ['Variant', '=']
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_frameshift(self):
        statement = 'variant(p.Thr1220Lysfs)'
        expected = ['Variant', 'p.Thr1220Lysfs']
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_snp(self):
        statement = 'var(delCTT)'
        expected = ['Variant', 'delCTT']
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_chromosome_1(self):
        statement = 'variant(g.117199646_117199648delCTT)'
        expected = ['Variant', 'g.117199646_117199648delCTT']
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_chromosome_2(self):
        statement = 'var(c.1521_1523delCTT)'
        expected = ['Variant', 'c.1521_1523delCTT']
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_rna_del(self):
        statement = 'var(r.1653_1655delcuu)'
        expected = ['Variant', 'r.1653_1655delcuu']
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_protein_trunc_triple(self):
        statement = 'var(p.Cys65*)'
        result = self.parser.parseString(statement)
        expected = ['Variant', 'p.Cys65*']
        self.assertEqual(expected, result.asList())

    def test_protein_trunc_legacy(self):
        statement = 'var(p.65*)'
        result = self.parser.parseString(statement)
        expected = ['Variant', 'p.65*']
        self.assertEqual(expected, result.asList())


class TestPmod(unittest.TestCase):
    def setUp(self):
        self.parser = PmodParser()

    def test_pmod1(self):
        statement = 'pmod(Ph, Ser, 473)'
        result = self.parser.parseString(statement)

        expected = ['ProteinModification', 'Ph', 'Ser', 473]
        self.assertEqual(expected, result.asList())

    def test_pmod2(self):
        statement = 'pmod(Ph, Ser)'
        result = self.parser.parseString(statement)

        expected = ['ProteinModification', 'Ph', 'Ser']
        self.assertEqual(expected, result.asList())

    def test_pmod3(self):
        statement = 'pmod(Ph)'
        result = self.parser.parseString(statement)

        expected = ['ProteinModification', 'Ph']
        self.assertEqual(expected, result.asList())

    def test_pmod4(self):
        statement = 'pmod(P, S, 9)'
        result = self.parser.parseString(statement)

        expected = ['ProteinModification', 'Ph', 'Ser', 9]
        self.assertEqual(expected, result.asList())

    def test_pmod5(self):
        statement = 'pmod(MOD:PhosRes, Ser, 473)'
        result = self.parser.parseString(statement)

        expected = ['ProteinModification', ['MOD', 'PhosRes'], 'Ser', 473]
        self.assertEqual(expected, result.asList())


class TestGmod(unittest.TestCase):
    def setUp(self):
        self.parser = GmodParser()

    def test_gmod_short(self):
        statement = 'gmod(M)'
        result = self.parser.parseString(statement)
        expected = ['GeneModification', 'Me']
        self.assertEqual(expected, result.asList())

    def test_gmod_unabbreviated(self):
        statement = 'gmod(Me)'
        result = self.parser.parseString(statement)
        expected = ['GeneModification', 'Me']
        self.assertEqual(expected, result.asList())

    def test_gmod_long(self):
        statement = 'geneModification(methylation)'
        result = self.parser.parseString(statement)
        expected = ['GeneModification', 'Me']
        self.assertEqual(expected, result.asList())


class TestPsub(unittest.TestCase):
    def setUp(self):
        self.parser = PsubParser()

    def test_psub_1(self):
        statement = 'sub(A, 127, Y)'
        result = self.parser.parseString(statement)

        expected_list = ['Variant', 'p.Ala127Tyr']
        self.assertEqual(expected_list, result.asList())

    def test_psub_2(self):
        statement = 'sub(Ala, 127, Tyr)'
        result = self.parser.parseString(statement)

        expected_list = ['Variant', 'p.Ala127Tyr']
        self.assertEqual(expected_list, result.asList())


class TestGsubParser(unittest.TestCase):
    def setUp(self):
        self.parser = GsubParser()

    def test_gsub(self):
        statement = 'sub(G,308,A)'
        result = self.parser.parseString(statement)

        expected_dict = ['Variant', 'g.308G>A']
        self.assertEqual(expected_dict, result.asList())


class TestFragmentParser(unittest.TestCase):
    """See http://openbel.org/language/web/version_2.0/bel_specification_version_2.0.html#_examples_2"""

    def setUp(self):
        self.parser = FragmentParser()

    def test_known_length(self):
        """test known length"""
        s = 'frag(5_20)'
        result = self.parser.parseString(s)
        expected = {
            'start': 5,
            'stop': 20
        }
        self.assertEqual(expected, result.asDict())

    def test_unknown_length(self):
        """amino-terminal fragment of unknown length"""
        s = 'frag(1_?)'
        result = self.parser.parseString(s)
        expected = {
            'start': 1,
            'stop': '?'
        }
        self.assertEqual(expected, result.asDict())

    def test_unknown_start_stop(self):
        """fragment with unknown start/stop"""
        s = 'frag(?_*)'
        result = self.parser.parseString(s)
        expected = {
            'start': '?',
            'stop': '*'
        }
        self.assertEqual(expected, result.asDict())

    def test_descriptor(self):
        """fragment with unknown start/stop and a descriptor"""
        s = 'frag(?, 55kD)'
        result = self.parser.parseString(s)
        expected = {
            'missing': '?',
            'description': '55kD'
        }
        self.assertEqual(expected, result.asDict())


class TestTruncationParser(unittest.TestCase):
    def setUp(self):
        self.parser = TruncParser()

    def test_trunc_1(self):
        statement = 'trunc(40)'
        result = self.parser.parseString(statement)

        expected = ['Variant', 'p.40*']
        self.assertEqual(expected, result.asList())


class TestFusionParser(unittest.TestCase):
    def setUp(self):
        self.parser = FusionParser()

    def test_261a(self):
        """RNA abundance of fusion with known breakpoints"""
        statement = 'fus(HGNC:TMPRSS2, r.1_79, HGNC:ERG, r.312_5034)'
        result = ['Fusion', ['HGNC', 'TMPRSS2'], ['r', 1, 79], ['HGNC', 'ERG'], ['r', 312, 5034]]
        self.assertEqual(result, self.parser.parseString(statement).asList())

    def test_261b(self):
        """RNA abundance of fusion with unspecified breakpoints"""
        statement = 'fus(HGNC:TMPRSS2, ?, HGNC:ERG, ?)'
        expected = ['Fusion', ['HGNC', 'TMPRSS2'], '?', ['HGNC', 'ERG'], '?']
        self.assertEqual(expected, self.parser.parseString(statement).asList())


class TestLocation(unittest.TestCase):
    def setUp(self):
        self.parser = LocationParser()

    def test_a(self):
        statement = 'loc(GOCC:intracellular)'
        result = self.parser.parseString(statement)
        expected = {
            'location': dict(namespace='GOCC', name='intracellular')
        }
        self.assertEqual(expected, result.asDict())
