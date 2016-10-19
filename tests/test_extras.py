import unittest

from pybel.parser.baseparser import nest, BaseParser
from pybel.parser.language import amino_acid
from pybel.parser.parse_exceptions import PlaceholderAminoAcidException
from pybel.exceptions import PyBelWarning
from pybel.parser.parse_identifier import IdentifierParser


class TestRandom(unittest.TestCase):
    def test_nest_failure(self):
        with self.assertRaises(ValueError):
            nest()

    def test_bad_subclass(self):
        class BadParser(BaseParser):
            pass

        with self.assertRaises(Exception):
            BadParser().get_language()

    def test_good_subclass(self):
        class GoodParser(BaseParser):
            def __init__(self):
                self.language = 5

        self.assertIsNotNone(GoodParser().get_language())

    def test_bad_aminoAcid(self):
        with self.assertRaises(PlaceholderAminoAcidException):
            amino_acid.parseString('X')

    def test_pybelexception_str(self):
        e = PyBelWarning('XXX')
        self.assertEqual("PyBEL100 - XXX", str(e))

        with self.assertRaises(PyBelWarning):
            raise e

    def test_unimplemented_mapping(self):
        with self.assertRaises(NotImplementedError):
            IdentifierParser(mapping={})
