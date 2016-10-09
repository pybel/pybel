from pybel.parser.baseparser import nest, BaseParser
from pybel.parser.language import amino_acid
from pybel.parser.parse_exceptions import PlaceholderAminoAcidException
import unittest

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

