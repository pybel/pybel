# -*- coding: utf-8 -*-

import unittest

from pybel.constants import DIRTY
from pybel.parser.exc import NakedNameWarning
from pybel.parser.parse_identifier import IdentifierParser


class TestIdentifierParser(unittest.TestCase):
    def setUp(self):
        self.namespace_to_term = {
            'A': dict(zip('123','PPP')),
            'B': dict(zip('456','PPP')),
        }
        self.parser = IdentifierParser(namespace_to_term=self.namespace_to_term)

    def test_valid_1(self):
        s = 'A:3'
        result = self.parser.parseString(s)

        self.assertIn('namespace', result)
        self.assertIn('name', result)
        self.assertEqual('A', result['namespace'])
        self.assertEqual('3', result['name'])

    def test_valid_2(self):
        s = 'A:"3"'
        result = self.parser.parseString(s)

        self.assertIn('namespace', result)
        self.assertIn('name', result)
        self.assertEqual('A', result['namespace'])
        self.assertEqual('3', result['name'])

    def test_invalid_1(self):
        s = 'C:4'
        with self.assertRaises(Exception):
            self.parser.parseString(s)

    def test_invalid_2(self):
        s = 'A:4'
        with self.assertRaises(Exception):
            self.parser.parseString(s)

    def test_invalid_3(self):
        s = 'bare'
        with self.assertRaises(NakedNameWarning):
            self.parser.parseString(s)

    def test_invalid_4(self):
        s = '"quoted"'
        with self.assertRaises(NakedNameWarning):
            self.parser.parseString(s)


class TestNamespaceParserDefault(unittest.TestCase):
    def setUp(self):
        namespace_to_term = {
            'A': dict(zip('123', 'PPP')),
            'B': dict(zip('456', 'PPP')),
        }

        default_namespace = {'X', 'Y', 'W Z'}
        self.parser = IdentifierParser(namespace_to_term=namespace_to_term, default_namespace=default_namespace)

    def test_valid_1(self):
        s = 'A:3'
        result = self.parser.parseString(s)

        self.assertIn('namespace', result)
        self.assertIn('name', result)
        self.assertEqual('A', result['namespace'])
        self.assertEqual('3', result['name'])

    def test_valid_2(self):
        s = 'X'
        result = self.parser.parseString(s)

        self.assertIn('name', result)
        self.assertEqual('X', result['name'])

    def test_valid_3(self):
        s = '"W Z"'
        result = self.parser.parseString(s)

        self.assertIn('name', result)
        self.assertEqual('W Z', result['name'])

    def test_not_in_defaultNs(self):
        s = 'D'
        with self.assertRaises(Exception):
            self.parser.parseString(s)


class TestNamespaceParserLenient(unittest.TestCase):
    def setUp(self):
        namespace_to_term = {
            'A': dict(zip('123', 'PPP')),
            'B': dict(zip('456', 'PPP')),
        }

        self.parser = IdentifierParser(namespace_to_term=namespace_to_term, allow_naked_names=True)

    def test_valid_1(self):
        s = 'A:3'
        result = self.parser.parseString(s)

        self.assertIn('namespace', result)
        self.assertIn('name', result)
        self.assertEqual('A', result['namespace'])
        self.assertEqual('3', result['name'])

    def test_valid_2(self):
        s = 'A:"3"'
        result = self.parser.parseString(s)

        self.assertIn('namespace', result)
        self.assertIn('name', result)
        self.assertEqual('A', result['namespace'])
        self.assertEqual('3', result['name'])

    def test_invalid_1(self):
        s = 'C:4'
        with self.assertRaises(Exception):
            self.parser.parseString(s)

    def test_invalid_2(self):
        s = 'A:4'
        with self.assertRaises(Exception):
            self.parser.parseString(s)

    def test_not_invalid_3(self):
        s = 'bare'
        result = self.parser.parseString(s)

        self.assertEqual(DIRTY, result['namespace'])
        self.assertEqual('bare', result['name'])

    def test_not_invalid_4(self):
        s = '"quoted"'
        result = self.parser.parseString(s)
        self.assertEqual(DIRTY, result['namespace'])
        self.assertEqual('quoted', result['name'])
