# -*- coding: utf-8 -*-

import os
import unittest
from pathlib import Path

from pybel.parser.baseparser import nest, BaseParser
from pybel.parser.language import amino_acid
from pybel.parser.parse_exceptions import PlaceholderAminoAcidWarning
from pybel.parser.parse_identifier import IdentifierParser
from pybel.utils import download_url
from tests.constants import test_an_1

dir_path = os.path.dirname(os.path.realpath(__file__))


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
        with self.assertRaises(PlaceholderAminoAcidWarning):
            amino_acid.parseString('X')

    def test_unimplemented_mapping(self):
        with self.assertRaises(NotImplementedError):
            IdentifierParser(mapping={})

    def test_download_url(self):
        res = download_url(Path(test_an_1).as_uri())

        expected_values = {
            'TestAnnot1': 'O',
            'TestAnnot2': 'O',
            'TestAnnot3': 'O',
            'TestAnnot4': 'O',
            'TestAnnot5': 'O'
        }

        self.assertEqual(expected_values, res['Values'])
