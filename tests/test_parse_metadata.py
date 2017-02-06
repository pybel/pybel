# -*- coding: utf-8 -*-

import logging
import unittest
from pathlib import Path

from pybel.manager.cache import CacheManager
from pybel.parser import ControlParser, MetadataParser
from pybel.parser.parse_exceptions import *
from pybel.parser.utils import sanitize_file_lines, split_file_to_annotations_and_definitions
from tests.constants import HGNC_KEYWORD, HGNC_URL, MESH_DISEASES_KEYWORD, MESH_DISEASES_URL, help_check_hgnc
from tests.constants import test_an_1, test_ns_1, test_bel, mock_bel_resources, test_citation_bel

logging.getLogger("requests").setLevel(logging.WARNING)


class TestSplitLines(unittest.TestCase):
    def test_parts(self):
        with open(test_bel) as f:
            docs, definitions, statements = split_file_to_annotations_and_definitions(f)

        self.assertEqual(7, len(docs))
        self.assertEqual(4, len(definitions))
        self.assertEqual(14, len(statements))


class TestParseMetadata(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.connection = 'sqlite://'
        cls.cm = CacheManager(cls.connection)
        cls.cm.create_database()

    def setUp(self):
        self.parser = MetadataParser(cache_manager=CacheManager(self.connection))

    @mock_bel_resources
    def test_namespace_name_persistience(self, mock_get):
        """Tests that a namespace defined by a URL can't be overwritten by a definition by another URL"""
        s = 'DEFINE NAMESPACE {} AS URL "{}"'.format(HGNC_KEYWORD, HGNC_URL)
        self.parser.parseString(s)
        help_check_hgnc(self, self.parser.namespace_dict)

        # Test doesn't overwrite
        s = 'DEFINE NAMESPACE {} AS URL "{}"'.format(HGNC_KEYWORD, 'XXXXX')
        self.parser.parseString(s)
        help_check_hgnc(self, self.parser.namespace_dict)

    @mock_bel_resources
    def test_annotation_name_persistience_1(self, mock_get):
        """Tests that an annotation defined by a URL can't be overwritten by a definition by a list"""

        s = 'DEFINE ANNOTATION {} AS URL "{}"'.format(MESH_DISEASES_KEYWORD, MESH_DISEASES_URL)
        self.parser.parseString(s)
        self.assertIn(MESH_DISEASES_KEYWORD, self.parser.annotations_dict)

        s = 'DEFINE ANNOTATION {} AS LIST {{"A","B","C"}}'.format(MESH_DISEASES_KEYWORD)
        self.parser.parseString(s)
        self.assertIn(MESH_DISEASES_KEYWORD, self.parser.annotations_dict)
        self.assertNotIn('A', self.parser.annotations_dict[MESH_DISEASES_KEYWORD])

    def test_annotation_name_persistience_2(self):
        """Tests that an annotation defined by a list can't be overwritten by a definition by URL"""
        s = 'DEFINE ANNOTATION TextLocation AS LIST {"Abstract","Results","Legend","Review"}'
        self.parser.parseString(s)
        self.assertIn('TextLocation', self.parser.annotations_dict)

        s = 'DEFINE ANNOTATION TextLocation AS URL "{}"'.format(MESH_DISEASES_URL)
        self.parser.parseString(s)
        self.assertIn('TextLocation', self.parser.annotations_dict)
        self.assertIn('Abstract', self.parser.annotations_dict['TextLocation'])

    def test_underscore(self):
        """Tests that an underscore is a valid character in an annotation name"""
        s = 'DEFINE ANNOTATION Text_Location AS LIST {"Abstract","Results","Legend","Review"}'
        self.parser.parseString(s)
        self.assertIn('Text_Location', self.parser.annotations_dict)

    @mock_bel_resources
    def test_control_compound(self, mock_get):
        lines = [
            'DEFINE ANNOTATION {} AS URL "{}"'.format(MESH_DISEASES_KEYWORD, MESH_DISEASES_URL),
            'DEFINE NAMESPACE {} AS URL "{}"'.format(HGNC_KEYWORD, HGNC_URL),
            'DEFINE ANNOTATION TextLocation AS LIST {"Abstract","Results","Legend","Review"}'
        ]
        self.parser.parse_lines(lines)

        self.assertIn(MESH_DISEASES_KEYWORD, self.parser.annotations_dict)
        self.assertIn(HGNC_KEYWORD, self.parser.namespace_dict)
        self.assertIn('TextLocation', self.parser.annotations_dict)

    def test_document_metadata_exception(self):
        s = 'SET DOCUMENT InvalidKey = "nope"'
        with self.assertRaises(InvalidMetadataException):
            self.parser.parseString(s)

    def test_parse_document(self):
        s = '''SET DOCUMENT Name = "Alzheimer's Disease Model"'''

        self.parser.parseString(s)

        self.assertIn('name', self.parser.document_metadata)
        self.assertEqual("Alzheimer's Disease Model", self.parser.document_metadata['name'])

    def test_parse_namespace_url_file(self):
        """Tests parsing a namespace by file URL"""
        s = 'DEFINE NAMESPACE TESTNS1 AS URL "{}"'.format(Path(test_ns_1).as_uri())
        self.parser.parseString(s)

        expected_values = {
            'TestValue1': {'O'},
            'TestValue2': {'O'},
            'TestValue3': {'O'},
            'TestValue4': {'O'},
            'TestValue5': {'O'}
        }

        self.assertIn('TESTNS1', self.parser.namespace_dict)

        for k, values in expected_values.items():
            self.assertIn(k, self.parser.namespace_dict['TESTNS1'])
            self.assertEqual(set(values), set(self.parser.namespace_dict['TESTNS1'][k]))

    def test_parse_annotation_url_file(self):
        """Tests parsing an annotation by file URL"""
        s = '''DEFINE ANNOTATION TESTAN1 AS URL "{}"'''.format(Path(test_an_1).as_uri())
        self.parser.parseString(s)

        expected_values = {
            'TestAnnot1': 'O',
            'TestAnnot2': 'O',
            'TestAnnot3': 'O',
            'TestAnnot4': 'O',
            'TestAnnot5': 'O'
        }

        self.assertIn('TESTAN1', self.parser.annotations_dict)
        self.assertEqual(expected_values, self.parser.annotations_dict['TESTAN1'])

    # FIXME
    '''
    def test_lexicography_namespace(self):
        s = 'DEFINE NAMESPACE hugo AS URL "{}"'.format(HGNC_URL)
        with self.assertRaises(LexicographyWarning):
            self.parser.parseString(s)

    def test_lexicography_annotation(self):
        s = 'DEFINE ANNOTATION mesh AS URL "{}"'.format(MESH_DISEASES_URL)
        with self.assertRaises(LexicographyWarning):
            self.parser.parseString(s)

    '''

    def test_parse_annotation_pattern(self):
        s = 'DEFINE ANNOTATION Test AS PATTERN "\w+"'
        with self.assertRaises(NotImplementedError):
            self.parser.parseString(s)

    def test_define_namespace_regex(self):
        s = 'DEFINE NAMESPACE dbSNP AS PATTERN "rs[0-9]*"'
        self.parser.parseString(s)

        self.assertNotIn('dbSNP', self.parser.namespace_dict)
        self.assertIn('dbSNP', self.parser.namespace_re)
        self.assertEqual('rs[0-9]*', self.parser.namespace_re['dbSNP'])


class TestParseControl(unittest.TestCase):
    def setUp(self):
        custom_annotations = {
            'Custom1': {'Custom1_A', 'Custom1_B'},
            'Custom2': {'Custom2_A', 'Custom2_B'}
        }

        self.parser = ControlParser(valid_annotations=custom_annotations)

    def test_set_statement_group(self):
        s = 'SET STATEMENT_GROUP = "my group"'

        self.assertIsNotNone(self.parser.set_statement_group.parseString(s))

        self.parser.parseString(s)
        self.assertEqual('my group', self.parser.statement_group)

        s = 'UNSET STATEMENT_GROUP'
        self.parser.parseString(s)
        self.assertIsNone(self.parser.statement_group)

    def test_unset_missing_evidence(self):
        s = [
            test_citation_bel,
            'UNSET Evidence'
        ]
        with self.assertRaises(MissingAnnotationKeyWarning):
            self.parser.parse_lines(s)

    def test_unset_missing_command(self):
        s = 'UNSET Custom1'
        with self.assertRaises(MissingAnnotationKeyWarning):
            self.parser.parseString(s)

    def test_unset_invalid_command(self):
        s = 'UNSET Custom3'
        with self.assertRaises(UndefinedAnnotationWarning):
            self.parser.parseString(s)

    def test_unset_missing_citation(self):
        s = [
            test_citation_bel,
            'UNSET Citation'
        ]
        self.parser.parse_lines(s)

    def test_set_missing_statement(self):
        s = 'SET MissingKey = "lol"'
        with self.assertRaises(UndefinedAnnotationWarning):
            self.parser.parseString(s)

    def test_invalid_citation_type(self):
        with self.assertRaises(InvalidCitationType):
            self.parser.parseString('SET Citation = {"PubMedCentral","Trends in molecular medicine","12928037"}')

    def test_invalid_pmid(self):
        with self.assertRaises(InvalidPubMedIdentifierWarning):
            self.parser.parseString('SET Citation = {"PubMed","Trends in molecular medicine","NOT VALID NUMBER"}')

    def test_citation_short(self):
        s = 'SET Citation = {"PubMed","Trends in molecular medicine","12928037"}'

        self.parser.parseString(s)

        expected_citation = {
            'type': 'PubMed',
            'name': 'Trends in molecular medicine',
            'reference': '12928037',
        }

        self.assertEqual(expected_citation, self.parser.citation)

        annotations = self.parser.get_annotations()
        expected_annotations = {
            'citation': {
                'type': 'PubMed',
                'name': 'Trends in molecular medicine',
                'reference': '12928037'
            }
        }
        self.assertEqual(expected_annotations, annotations)

        self.parser.parseString('UNSET Citation')
        self.assertEqual(0, len(self.parser.citation))

    def test_citation_long(self):
        s = 'SET Citation = {"PubMed","Trends in molecular medicine","12928037","","de Nigris|Lerman A|Ignarro LJ",""}'

        self.parser.parseString(s)

        expected_citation = {
            'type': 'PubMed',
            'name': 'Trends in molecular medicine',
            'reference': '12928037',
            'date': '',
            'authors': 'de Nigris|Lerman A|Ignarro LJ',
            'comments': ''
        }

        self.assertEqual(expected_citation, self.parser.citation)

    def test_citation_error(self):
        s = 'SET Citation = {"PubMed","Trends in molecular medicine"}'
        with self.assertRaises(InvalidCitationException):
            self.parser.parseString(s)

    def test_evidence(self):
        s = 'SET Evidence = "For instance, during 7-ketocholesterol-induced apoptosis of U937 cells"'
        self.parser.parseString(s)

        expected_annotation = {
            'SupportingText': 'For instance, during 7-ketocholesterol-induced apoptosis of U937 cells'
        }

        self.assertEqual(expected_annotation, self.parser.annotations)

    def test_custom_annotation(self):
        s = 'SET Custom1 = "Custom1_A"'
        self.parser.parseString(s)

        expected_annotation = {
            'Custom1': 'Custom1_A'
        }

        self.assertEqual(expected_annotation, self.parser.annotations)

    def test_custom_annotation_list(self):
        s = 'SET Custom1 = {"Custom1_A","Custom1_B"}'
        self.parser.parseString(s)

        expected_annotation = {
            'Custom1': {'Custom1_A', 'Custom1_B'}
        }

        self.assertEqual(expected_annotation, self.parser.annotations)

    def test_custom_annotation_list_withInvalid(self):
        s = 'SET Custom1 = {"Custom1_A","Custom1_B","Evil invalid!!!"}'

        with self.assertRaises(IllegalAnnotationValueWarning):
            self.parser.parseString(s)

    def test_custom_key_failure(self):
        s = 'SET FAILURE = "never gonna happen"'
        with self.assertRaises(UndefinedAnnotationWarning):
            self.parser.parseString(s)

    def test_custom_value_failure(self):
        s = 'SET Custom1 = "Custom1_C"'
        with self.assertRaises(IllegalAnnotationValueWarning):
            self.parser.parseString(s)

    def test_reset_annotation(self):
        s1 = 'SET Evidence = "a"'
        s2 = 'SET Evidence = "b"'

        self.parser.parseString(s1)
        self.parser.parseString(s2)

        self.assertEqual('b', self.parser.annotations['SupportingText'])

    def test_unset_evidence(self):
        s1 = 'SET Evidence = "a"'
        s2 = 'UNSET Evidence'

        self.parser.parseString(s1)
        self.parser.parseString(s2)

        self.assertEqual({}, self.parser.annotations)

    def test_unset_custom(self):
        s1 = 'SET Custom1 = "Custom1_A"'
        s2 = 'UNSET Custom1'

        self.parser.parseString(s1)
        self.parser.parseString(s2)

        self.assertEqual({}, self.parser.annotations)

    def test_reset_citation(self):
        s1 = 'SET Citation = {"PubMed","Test Reference 1","11111"}'
        s2 = 'SET Evidence = "d"'

        s3 = 'SET Citation = {"PubMed","Test Reference 2","22222"}'
        s4 = 'SET Evidence = "h"'
        s5 = 'SET Custom1 = "Custom1_A"'
        s6 = 'SET Custom2 = "Custom2_A"'

        self.parser.parse_lines([s1, s2, s3, s4, s5, s6])

        self.assertEqual('h', self.parser.annotations['SupportingText'])
        self.assertEqual('PubMed', self.parser.citation['type'])
        self.assertEqual('Test Reference 2', self.parser.citation['name'])
        self.assertEqual('22222', self.parser.citation['reference'])

        self.parser.parseString('UNSET {"Custom1","Evidence"}')
        self.assertNotIn('Custom1', self.parser.annotations)
        self.assertNotIn('SupportingText', self.parser.annotations)
        self.assertIn('Custom2', self.parser.annotations)
        self.assertNotEqual(0, len(self.parser.citation))

        self.parser.parseString('UNSET ALL')
        self.assertEqual(0, len(self.parser.annotations))
        self.assertEqual(0, len(self.parser.citation))


class TestParseEvidence(unittest.TestCase):
    def test_111(self):
        statement = '''SET Evidence = "1.1.1 Easy case"'''
        expect = '''SET Evidence = "1.1.1 Easy case'''
        lines = list(sanitize_file_lines(statement.split('\n')))
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertTrue(expect, line)

    def test_131(self):
        statement = '''SET Evidence = "3.1 Backward slash break test \\
second line"'''
        expect = '''SET Evidence = "3.1 Backward slash break test second line"'''
        lines = [line for i, line in sanitize_file_lines(statement.split('\n'))]
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertEqual(expect, line)

    def test_132(self):
        statement = '''SET Evidence = "3.2 Backward slash break test with whitespace \\
second line"'''
        expect = '''SET Evidence = "3.2 Backward slash break test with whitespace second line"'''
        lines = [line for i, line in sanitize_file_lines(statement.split('\n'))]
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertEqual(expect, line)

    def test_133(self):
        statement = '''SET Evidence = "3.3 Backward slash break test \\
second line \\
third line"'''
        expect = '''SET Evidence = "3.3 Backward slash break test second line third line"'''
        lines = [line for i, line in sanitize_file_lines(statement.split('\n'))]
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertEqual(expect, line)

    def test_141(self):
        statement = '''SET Evidence = "4.1 Malformed line breakcase
second line"'''
        expect = '''SET Evidence = "4.1 Malformed line breakcase second line"'''
        lines = [line for i, line in sanitize_file_lines(statement.split('\n'))]
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertEqual(expect, line)

    def test_142(self):
        statement = '''SET Evidence = "4.2 Malformed line breakcase
second line
third line"'''
        expect = '''SET Evidence = "4.2 Malformed line breakcase second line third line"'''
        lines = [line for i, line in sanitize_file_lines(statement.split('\n'))]
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertEqual(expect, line)
