# -*- coding: utf-8 -*-

import logging
import unittest
from pathlib import Path

from pybel.manager.cache import CacheManager
from pybel.parser import MetadataParser
from pybel.parser.parse_exceptions import *
from tests.constants import HGNC_KEYWORD, HGNC_URL, MESH_DISEASES_KEYWORD, MESH_DISEASES_URL, help_check_hgnc
from tests.constants import test_an_1, test_ns_1, mock_bel_resources

logging.getLogger("requests").setLevel(logging.WARNING)


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

        # Check nothing bad happens
        # with self.assertLogs('pybel', level='WARNING'):
        self.parser.parseString(s)

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
        self.parser.parseString(s)

        self.assertNotIn('Test', self.parser.annotations_dict)
        self.assertIn('Test', self.parser.annotations_re)
        self.assertEqual('\w+', self.parser.annotations_re['Test'])

    def test_define_namespace_regex(self):
        s = 'DEFINE NAMESPACE dbSNP AS PATTERN "rs[0-9]*"'
        self.parser.parseString(s)

        self.assertNotIn('dbSNP', self.parser.namespace_dict)
        self.assertIn('dbSNP', self.parser.namespace_re)
        self.assertEqual('rs[0-9]*', self.parser.namespace_re['dbSNP'])
