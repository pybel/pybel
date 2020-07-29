# -*- coding: utf-8 -*-

import re
import unittest

from pybel.constants import DIRTY
from pybel.exceptions import MissingNamespaceRegexWarning, NakedNameWarning
from pybel.parser import ConceptParser


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


class TestConceptEnumerated(_ParserMixin):
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


class TestConceptParserDefault(_ParserMixin):
    """Tests where the concept parser allows an enumerated list of unqualified entities."""

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
        self.assertNotIn('identifier', result)
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
        self.assertNotIn('identifier', result)
        self.assertEqual('W Z', result['name'])

    def test_not_in_defaultNs(self):
        s = 'D'
        with self.assertRaises(Exception):
            self.parser.parseString(s)


class TestConceptParserLenient(_ParserMixin):
    """Tests where naked names are allowed."""

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
        self.assertNotIn('identifier', result)
        self.assertEqual('A', result['namespace'])
        self.assertEqual('3', result['name'])

    def test_valid_2(self):
        s = 'A:"3"'
        result = self.parser.parseString(s)

        self.assertIn('namespace', result)
        self.assertIn('name', result)
        self.assertNotIn('identifier', result)
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

        self.assertIn('namespace', result)
        self.assertIn('name', result)
        self.assertNotIn('identifier', result)
        self.assertEqual(DIRTY, result['namespace'])
        self.assertEqual('bare', result['name'])

    def test_not_invalid_4(self):
        s = '"quoted"'
        result = self.parser.parseString(s)

        self.assertIn('namespace', result)
        self.assertIn('name', result)
        self.assertNotIn('identifier', result)
        self.assertEqual(DIRTY, result['namespace'])
        self.assertEqual('quoted', result['name'])


class TestConceptParserRegex(unittest.TestCase):
    """Tests for regular expression parsing"""

    def setUp(self) -> None:
        self.parser = ConceptParser(namespace_to_pattern={
            'hgnc': re.compile(r'\d+'),
            'ec-code': re.compile(r'.+'),
        })
        self.assertEqual({}, self.parser.namespace_to_identifier_to_encoding)
        self.assertEqual({}, self.parser.namespace_to_name_to_encoding)

    def test_valid(self):
        for curie, namespace, name in [
            ('hgnc:391', 'hgnc', '391'),
            ('ec-code:1.1.1.27', 'ec-code', '1.1.1.27'),
        ]:
            with self.subTest(curie=curie):
                result = self.parser.parseString(curie)
                self.assertIn('namespace', result)
                self.assertIn('name', result)
                self.assertNotIn('identifier', result)
                self.assertEqual(namespace, result['namespace'])
                self.assertEqual(name, result['name'])

    def test_invalid(self):
        """Test invalid BEL term."""
        s = 'hgnc:AKT1'
        with self.assertRaises(MissingNamespaceRegexWarning):
            result = self.parser.parseString(s)
            print(result.asDict())

    def test_valid_obo(self):
        """Test parsing an identifier that has a name."""
        s = 'hgnc:391 ! AKT1'
        result = self.parser.parseString(s)

        self.assertIn('namespace', result)
        self.assertIn('name', result)
        self.assertIn('identifier', result)
        self.assertEqual('hgnc', result['namespace'])
        self.assertEqual('AKT1', result['name'])
        self.assertEqual('391', result['identifier'])

    def test_invalid_obo(self):
        """Test parsing an OBO-style identifier where the identifier and name are switched."""
        s = 'hgnc:AKT1 ! 391'
        with self.assertRaises(MissingNamespaceRegexWarning):
            result = self.parser.parseString(s)
            print(result.asDict())
