# -*- coding: utf-8 -*-

import unittest

from pybel.constants import DIRTY
from pybel.parser import ConceptParser
from pybel.parser.exc import NakedNameWarning


class _ParserMixin(unittest.TestCase):
    def setUp(self):
        self.namespace_to_term = {
            'A': {
                (None, '1'): 'P',
                (None, '2'): 'P',
                (None, '3'): 'P',
            },
            'B': {
                (None, '4'): 'P',
                (None, '5'): 'P',
                (None, '6'): 'P',
            }
        }


class TestIdentifierParser(_ParserMixin):
    def setUp(self):
        super().setUp()
        self.parser = ConceptParser(namespace_to_term_to_encoding=self.namespace_to_term)

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


class TestNamespaceParserDefault(_ParserMixin):
    def setUp(self):
        super().setUp()
        default_namespace = {'X', 'Y', 'W Z'}
        self.parser = ConceptParser(
            namespace_to_term_to_encoding=self.namespace_to_term,
            default_namespace=default_namespace,
        )

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


class TestNamespaceParserLenient(_ParserMixin):
    def setUp(self):
        super().setUp()
        self.parser = ConceptParser(
            namespace_to_term_to_encoding=self.namespace_to_term,
            allow_naked_names=True,
        )

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
