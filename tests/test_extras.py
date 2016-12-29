import os
import unittest

import pybel
from pybel.exceptions import PyBelWarning
from pybel.parser.baseparser import nest, BaseParser
from pybel.parser.language import amino_acid
from pybel.parser.parse_exceptions import PlaceholderAminoAcidException
from pybel.parser.parse_identifier import IdentifierParser
from pybel.utils import download_url

dir_path = os.path.dirname(os.path.realpath(__file__))


class TestRandom(unittest.TestCase):
    def test_nest_failure(self):
        with self.assertRaises(ValueError):
            nest()

    def test_database_notimplemented(self):
        with self.assertRaises(NotImplementedError):
            pybel.graph.from_database('')

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
        self.assertEqual("PyBEL100 - PyBelWarning - XXX", str(e))

        with self.assertRaises(PyBelWarning):
            raise e

    def test_unimplemented_mapping(self):
        with self.assertRaises(NotImplementedError):
            IdentifierParser(mapping={})

    def test_download_url(self):
        path = os.path.join(dir_path, 'bel', 'test_an_1.belanno')
        res = download_url('file://{}'.format(path))

        expected_values = {
            'TestAnnot1': 'O',
            'TestAnnot2': 'O',
            'TestAnnot3': 'O',
            'TestAnnot4': 'O',
            'TestAnnot5': 'O'
        }

        self.assertEqual(expected_values, res['Values'])
