# -*- coding: utf-8 -*-

"""Tests for PyBEL utilities."""

import unittest

import time
from six import string_types

from pybel.parser.exc import PlaceholderAminoAcidWarning
from pybel.parser.modifiers.constants import amino_acid
from pybel.parser.utils import nest
from pybel.resources.definitions import get_bel_resource
from pybel.resources.exc import EmptyResourceError
from pybel.resources.utils import get_iso_8601_date
from pybel.testing.constants import test_an_1, test_ns_empty
from pybel.testing.mocks import mock_bel_resources
from pybel.utils import expand_dict, flatten_dict, tokenize_version


class TestTokenizeVersion(unittest.TestCase):
    """Test tokenization of version strings."""

    def test_simple(self):
        """Test the simplest version string case."""
        version_str = '0.1.2'
        version_tuple = 0, 1, 2
        self.assertEqual(version_tuple, tokenize_version(version_str))

    def test_long(self):
        """Test when the version pieces have more than 1 digit."""
        version_str = '0.12.20'
        version_tuple = 0, 12, 20
        self.assertEqual(version_tuple, tokenize_version(version_str))

    def test_dev(self):
        """Test when there's a dash after."""
        version_str = '0.1.2-dev'
        version_tuple = 0, 1, 2
        self.assertEqual(version_tuple, tokenize_version(version_str))


class TestRandom(unittest.TestCase):
    def test_nest_failure(self):
        with self.assertRaises(ValueError):
            nest()

    def test_bad_aminoAcid(self):
        with self.assertRaises(PlaceholderAminoAcidWarning):
            amino_acid.parseString('X')

    def test_get_date(self):
        d = get_iso_8601_date()
        self.assertIsInstance(d, string_types)
        self.assertEqual(d[:4], time.strftime('%Y'))
        self.assertEqual(d[4:6], time.strftime('%m'))
        self.assertEqual(d[6:8], time.strftime('%d'))


class TestUtils(unittest.TestCase):
    def test_download_url(self):
        """Test downloading a resource by URL."""
        with mock_bel_resources:
            res = get_bel_resource(test_an_1)

        expected_values = {
            'TestAnnot1': 'O',
            'TestAnnot2': 'O',
            'TestAnnot3': 'O',
            'TestAnnot4': 'O',
            'TestAnnot5': 'O'
        }

        self.assertEqual(expected_values, res['Values'])

    def test_download_raises_on_empty(self):
        """Test that an error is thrown if an empty resource is downloaded."""
        with mock_bel_resources, self.assertRaises(EmptyResourceError):
            get_bel_resource(test_ns_empty)

    def test_expand_dict(self):
        flat_dict = {
            'k1': 'v1',
            'k2_k2a': 'v2',
            'k2_k2b': 'v3',
            'k2_k2c_k2ci': 'v4',
            'k2_k2c_k2cii': 'v5'
        }

        expected_dict = {
            'k1': 'v1',
            'k2': {
                'k2a': 'v2',
                'k2b': 'v3',
                'k2c': {
                    'k2ci': 'v4',
                    'k2cii': 'v5'
                }
            }
        }

        self.assertEqual(expected_dict, expand_dict(flat_dict))

    def test_flatten_dict(self):
        d = {
            'A': 5,
            'B': 'b',
            'C': {
                'D': 'd',
                'E': 'e'
            }
        }

        expected = {
            'A': 5,
            'B': 'b',
            'C_D': 'd',
            'C_E': 'e'
        }
        self.assertEqual(expected, flatten_dict(d))

    def test_flatten_dict_withLists(self):
        d = {
            'A': 5,
            'B': 'b',
            'C': {
                'D': ['d', 'delta'],
                'E': 'e'
            }
        }

        expected = {
            'A': 5,
            'B': 'b',
            'C_D': 'd,delta',
            'C_E': 'e'
        }
        self.assertEqual(expected, flatten_dict(d))
