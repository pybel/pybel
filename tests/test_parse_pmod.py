import unittest

from pybel.parser.parse_pmod import PmodParser


class TestPmod(unittest.TestCase):
    def setUp(self):
        self.parser = PmodParser()

    def test_pmod1(self):
        statement = 'pmod(Ph, Ser, 473)'
        expected = ['ProteinModification', 'Ph', 'Ser', 473]
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_pmod2(self):
        statement = 'pmod(Ph, Ser)'
        expected = ['ProteinModification', 'Ph', 'Ser']
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_pmod3(self):
        statement = 'pmod(Ph)'
        expected = ['ProteinModification', 'Ph']
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_pmod4(self):
        statement = 'pmod(P, S, 9)'
        expected = ['ProteinModification', 'P', 'S', 9]
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asList())

    def test_pmod5(self):
        statement = 'pmod(MOD:PhosRes, Ser, 473)'
        expected = ['ProteinModification', ['MOD', 'PhosRes'], 'Ser', 473]
        result = self.parser.parseString(statement)
        self.assertEqual(expected, result.asList())
