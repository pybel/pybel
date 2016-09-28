import logging
import unittest

from pybel.parsers.hgvs_parser import *

log = logging.getLogger(__name__)


class TestVariants(unittest.TestCase):
    def test_protein_del(self):
        statement = 'p.Phe508del'
        expected = ['Phe', 508, 'del']
        result = hgvs_protein_del.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_protein_mut(self):
        statement = 'p.Gly576Ala'
        expected = ['Gly', 576, 'Ala']
        result = hgvs_protein_mut.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_unspecified(self):
        statement = '='
        expected = ['=']
        result = hgvs.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_frameshift(self):
        statement = 'p.Thr1220Lysfs'
        expected = ['Thr', 1220, 'Lys', 'fs']
        result = hgvs_protein_fs.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_snp(self):
        statement = 'delCTT'
        expected = ['del', 'CTT']
        result = hgvs_snp.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_chromosome(self):
        statement = 'g.117199646_117199648delCTT'
        expected = [117199646, 117199648, 'del', 'CTT']
        result = hgvs_chromosome.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_chromosome(self):
        statement = 'c.1521_1523delCTT'
        expected = [1521, 1523, 'del', 'CTT']
        result = hgvs_dna_del.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_rna_del(self):
        statement = 'r.1653_1655delcuu'
        expected = [1653, 1655, 'del', 'cuu']
        result = hgvs_rna_del.parseString(statement)
        self.assertEqual(expected, result.asList())
