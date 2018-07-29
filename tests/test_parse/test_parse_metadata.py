# -*- coding: utf-8 -*-

"""Test parsing metadata from a BEL script."""

import logging
import os
import unittest
from pathlib import Path

from pybel.parser import MetadataParser
from pybel.parser.exc import (
    InvalidMetadataException, RedefinedAnnotationError, RedefinedNamespaceError, VersionFormatWarning,
)
from pybel.resources.document import split_file_to_annotations_and_definitions
from pybel.testing.cases import FleetingTemporaryCacheMixin
from pybel.testing.constants import test_an_1, test_bel_simple, test_ns_1, test_ns_nocache_path
from pybel.testing.mocks import mock_bel_resources
from tests.constants import (
    HGNC_KEYWORD, HGNC_URL, MESH_DISEASES_KEYWORD, MESH_DISEASES_URL, help_check_hgnc,
)

logging.getLogger("requests").setLevel(logging.WARNING)


class TestSplitLines(unittest.TestCase):
    def test_parts(self):
        with open(test_bel_simple) as f:
            docs, definitions, statements = split_file_to_annotations_and_definitions(f)
        self.assertEqual(8, len(docs))
        self.assertEqual(4, len(definitions))
        self.assertEqual(14, len(statements))


class TestParseMetadata(FleetingTemporaryCacheMixin):
    def setUp(self):
        super(TestParseMetadata, self).setUp()
        self.parser = MetadataParser(manager=self.manager)

    def test_namespace_nocache(self):
        """Checks namespace is loaded into parser but not cached"""
        s = 'DEFINE NAMESPACE TESTNS3 AS URL "{}"'.format(test_ns_nocache_path)
        self.parser.parseString(s)
        self.assertIn('TESTNS3', self.parser.namespace_dict)
        self.assertEqual(0, len(self.manager.list_namespaces()))

    @mock_bel_resources
    def test_namespace_name_persistience(self, mock_get):
        """Tests that a namespace defined by a URL can't be overwritten by a definition by another URL"""
        s = 'DEFINE NAMESPACE {} AS URL "{}"'.format(HGNC_KEYWORD, HGNC_URL)
        self.parser.parseString(s)
        help_check_hgnc(self, self.parser.namespace_dict)

        s = 'DEFINE NAMESPACE {} AS URL "{}"'.format(HGNC_KEYWORD, 'XXXXX')
        with self.assertRaises(RedefinedNamespaceError):
            self.parser.parseString(s)

        help_check_hgnc(self, self.parser.namespace_dict)

    @mock_bel_resources
    def test_annotation_name_persistience_1(self, mock_get):
        """Tests that an annotation defined by a URL can't be overwritten by a definition by a list"""

        s = 'DEFINE ANNOTATION {} AS URL "{}"'.format(MESH_DISEASES_KEYWORD, MESH_DISEASES_URL)
        self.parser.parseString(s)
        self.assertIn(MESH_DISEASES_KEYWORD, self.parser.annotation_dict)

        s = 'DEFINE ANNOTATION {} AS LIST {{"A","B","C"}}'.format(MESH_DISEASES_KEYWORD)
        with self.assertRaises(RedefinedAnnotationError):
            self.parser.parseString(s)

        self.assertIn(MESH_DISEASES_KEYWORD, self.parser.annotation_dict)
        self.assertNotIn('A', self.parser.annotation_dict[MESH_DISEASES_KEYWORD])
        self.assertIn('46, XX Disorders of Sex Development', self.parser.annotation_dict[MESH_DISEASES_KEYWORD])

    def test_annotation_name_persistience_2(self):
        """Tests that an annotation defined by a list can't be overwritten by a definition by URL"""
        s = 'DEFINE ANNOTATION TextLocation AS LIST {"Abstract","Results","Legend","Review"}'
        self.parser.parseString(s)
        self.assertIn('TextLocation', self.parser.annotation_dict)

        s = 'DEFINE ANNOTATION TextLocation AS URL "{}"'.format(MESH_DISEASES_URL)
        with self.assertRaises(RedefinedAnnotationError):
            self.parser.parseString(s)

        self.assertIn('TextLocation', self.parser.annotation_dict)
        self.assertIn('Abstract', self.parser.annotation_dict['TextLocation'])

    def test_underscore(self):
        """Tests that an underscore is a valid character in an annotation name"""
        s = 'DEFINE ANNOTATION Text_Location AS LIST {"Abstract","Results","Legend","Review"}'
        self.parser.parseString(s)
        self.assertIn('Text_Location', self.parser.annotation_dict)

    @mock_bel_resources
    def test_control_compound(self, mock_get):
        lines = [
            'DEFINE ANNOTATION {} AS URL "{}"'.format(MESH_DISEASES_KEYWORD, MESH_DISEASES_URL),
            'DEFINE NAMESPACE {} AS URL "{}"'.format(HGNC_KEYWORD, HGNC_URL),
            'DEFINE ANNOTATION TextLocation AS LIST {"Abstract","Results","Legend","Review"}'
        ]
        self.parser.parse_lines(lines)

        self.assertIn(MESH_DISEASES_KEYWORD, self.parser.annotation_dict)
        self.assertIn(HGNC_KEYWORD, self.parser.namespace_dict)
        self.assertIn('TextLocation', self.parser.annotation_dict)

    @unittest.skipUnless('PYBEL_BASE' in os.environ, "Need local files to test local files")
    def test_squiggly_filepath(self):
        line = 'DEFINE NAMESPACE {} AS URL "~/dev/pybel/tests/belns/hgnc-human-genes.belns"'.format(HGNC_KEYWORD)
        self.parser.parseString(line)
        help_check_hgnc(self, self.parser.namespace_dict)

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

    @mock_bel_resources
    def test_parse_namespace_url_file(self, mock):
        """Tests parsing a namespace by file URL"""
        s = 'DEFINE NAMESPACE TESTNS1 AS URL "{}"'.format(test_ns_1)
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
        keyword = 'TESTAN1'
        url = Path(test_an_1).as_uri()
        line = 'DEFINE ANNOTATION {keyword} AS URL "{url}"'.format(
            keyword=keyword,
            url=url,
        )
        self.parser.parseString(line)

        expected_values = {
            'TestAnnot1': 'O',
            'TestAnnot2': 'O',
            'TestAnnot3': 'O',
            'TestAnnot4': 'O',
            'TestAnnot5': 'O'
        }

        self.assertEqual(set(expected_values), self.parser.manager.get_annotation_entry_names(url))

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

        self.assertNotIn('Test', self.parser.annotation_dict)
        self.assertIn('Test', self.parser.annotation_regex)
        self.assertEqual('\w+', self.parser.annotation_regex['Test'])

    def test_define_namespace_regex(self):
        s = 'DEFINE NAMESPACE dbSNP AS PATTERN "rs[0-9]*"'
        self.parser.parseString(s)

        self.assertNotIn('dbSNP', self.parser.namespace_dict)
        self.assertIn('dbSNP', self.parser.namespace_regex)
        self.assertEqual('rs[0-9]*', self.parser.namespace_regex['dbSNP'])

    def test_not_semantic_version(self):
        s = 'SET DOCUMENT Version = "1.0"'
        with self.assertRaises(VersionFormatWarning):
            self.parser.parseString(s)
