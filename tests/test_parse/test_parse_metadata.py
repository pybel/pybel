# -*- coding: utf-8 -*-

"""Test parsing metadata from a BEL script."""

import logging
import os
import re
import unittest
from pathlib import Path

from bel_resources.constants import ANNOTATION_URL_FMT, NAMESPACE_URL_FMT
from pybel.parser import MetadataParser
from pybel.parser.exc import (
    InvalidMetadataException, RedefinedAnnotationError, RedefinedNamespaceError, VersionFormatWarning,
)
from pybel.testing.cases import FleetingTemporaryCacheMixin
from pybel.testing.constants import test_an_1, test_ns_1, test_ns_nocache_path
from pybel.testing.mocks import mock_bel_resources
from tests.constants import (
    HGNC_KEYWORD, HGNC_URL, MESH_DISEASES_KEYWORD, MESH_DISEASES_URL, help_check_hgnc,
)

logging.getLogger("requests").setLevel(logging.WARNING)


class TestParseMetadata(FleetingTemporaryCacheMixin):
    def setUp(self):
        super(TestParseMetadata, self).setUp()
        self.parser = MetadataParser(manager=self.manager)

    def help_test_local_annotation(self, annotation: str) -> None:
        """Check that the annotation is defined locally."""
        self.assertTrue(self.parser.has_annotation(annotation))
        self.assertNotIn(annotation, self.parser.annotation_to_term)
        self.assertFalse(self.parser.has_enumerated_annotation(annotation))
        self.assertNotIn(annotation, self.parser.annotation_pattern)
        self.assertFalse(self.parser.has_regex_annotation(annotation))
        self.assertIn(annotation, self.parser.annotation_to_local)
        self.assertTrue(self.parser.has_local_annotation(annotation))

    def test_namespace_nocache(self):
        """Checks namespace is loaded into parser but not cached"""
        s = NAMESPACE_URL_FMT.format('TESTNS3', test_ns_nocache_path)
        self.parser.parseString(s)
        self.assertIn('TESTNS3', self.parser.namespace_to_term)
        self.assertEqual(0, len(self.manager.list_namespaces()))

    @mock_bel_resources
    def test_namespace_name_persistience(self, mock_get):
        """Tests that a namespace defined by a URL can't be overwritten by a definition by another URL"""
        s = NAMESPACE_URL_FMT.format(HGNC_KEYWORD, HGNC_URL)
        self.parser.parseString(s)
        help_check_hgnc(self, self.parser.namespace_to_term)

        s = NAMESPACE_URL_FMT.format(HGNC_KEYWORD, 'XXXXX')
        with self.assertRaises(RedefinedNamespaceError):
            self.parser.parseString(s)

        help_check_hgnc(self, self.parser.namespace_to_term)

    @mock_bel_resources
    def test_annotation_name_persistience_1(self, mock_get):
        """Tests that an annotation defined by a URL can't be overwritten by a definition by a list"""

        s = ANNOTATION_URL_FMT.format(MESH_DISEASES_KEYWORD, MESH_DISEASES_URL)
        self.parser.parseString(s)
        self.assertIn(MESH_DISEASES_KEYWORD, self.parser.annotation_to_term)

        s = 'DEFINE ANNOTATION {} AS LIST {{"A","B","C"}}'.format(MESH_DISEASES_KEYWORD)
        with self.assertRaises(RedefinedAnnotationError):
            self.parser.parseString(s)

        self.assertIn(MESH_DISEASES_KEYWORD, self.parser.annotation_to_term)
        self.assertNotIn('A', self.parser.annotation_to_term[MESH_DISEASES_KEYWORD])
        self.assertIn('46, XX Disorders of Sex Development', self.parser.annotation_to_term[MESH_DISEASES_KEYWORD])

    def test_annotation_name_persistience_2(self):
        """Tests that an annotation defined by a list can't be overwritten by a definition by URL"""
        s = 'DEFINE ANNOTATION TextLocation AS LIST {"Abstract","Results","Legend","Review"}'
        self.parser.parseString(s)
        self.help_test_local_annotation('TextLocation')

        s = ANNOTATION_URL_FMT.format('TextLocation', MESH_DISEASES_URL)
        with self.assertRaises(RedefinedAnnotationError):
            self.parser.parseString(s)

        self.help_test_local_annotation('TextLocation')
        self.assertIn('Abstract', self.parser.annotation_to_local['TextLocation'])

    def test_underscore(self):
        """Tests that an underscore is a valid character in an annotation name"""
        s = 'DEFINE ANNOTATION Text_Location AS LIST {"Abstract","Results","Legend","Review"}'
        self.parser.parseString(s)
        self.help_test_local_annotation('Text_Location')

    @mock_bel_resources
    def test_control_compound(self, mock_get):
        text_location = 'TextLocation'
        lines = [
            ANNOTATION_URL_FMT.format(MESH_DISEASES_KEYWORD, MESH_DISEASES_URL),
            NAMESPACE_URL_FMT.format(HGNC_KEYWORD, HGNC_URL),
            'DEFINE ANNOTATION TextLocation AS LIST {"Abstract","Results","Legend","Review"}'
        ]
        self.parser.parse_lines(lines)

        self.assertIn(MESH_DISEASES_KEYWORD, self.parser.annotation_to_term)
        self.assertIn(HGNC_KEYWORD, self.parser.namespace_to_term)
        self.help_test_local_annotation(text_location)

    @unittest.skipUnless('PYBEL_BASE' in os.environ, "Need local files to test local files")
    def test_squiggly_filepath(self):
        line = NAMESPACE_URL_FMT.format(HGNC_KEYWORD, "~/dev/pybel/src/pybel/testing/resources/belns/hgnc-names.belns")
        self.parser.parseString(line)
        help_check_hgnc(self, self.parser.namespace_to_term)

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
        s = NAMESPACE_URL_FMT.format('TESTNS1', test_ns_1)
        self.parser.parseString(s)

        expected_values = {
            'TestValue1': {'O'},
            'TestValue2': {'O'},
            'TestValue3': {'O'},
            'TestValue4': {'O'},
            'TestValue5': {'O'}
        }

        self.assertIn('TESTNS1', self.parser.namespace_to_term)

        for k, values in expected_values.items():
            self.assertIn(k, self.parser.namespace_to_term['TESTNS1'])
            self.assertEqual(set(values), set(self.parser.namespace_to_term['TESTNS1'][k]))

    def test_parse_annotation_url_file(self):
        """Tests parsing an annotation by file URL"""
        keyword = 'TESTAN1'
        url = Path(test_an_1).as_uri()
        line = ANNOTATION_URL_FMT.format(keyword, url)
        self.parser.parseString(line)

        expected_values = {
            'TestAnnot1': 'O',
            'TestAnnot2': 'O',
            'TestAnnot3': 'O',
            'TestAnnot4': 'O',
            'TestAnnot5': 'O'
        }

        self.assertEqual(set(expected_values), self.parser.manager.get_annotation_entry_names(url))

    def test_parse_annotation_pattern(self):
        s = r'DEFINE ANNOTATION Test AS PATTERN "\w+"'
        self.parser.parseString(s)

        self.assertNotIn('Test', self.parser.annotation_to_term)
        self.assertIn('Test', self.parser.annotation_to_pattern)
        self.assertEqual(re.compile(r'\w+'), self.parser.annotation_to_pattern['Test'])

    def test_define_namespace_regex(self):
        s = 'DEFINE NAMESPACE dbSNP AS PATTERN "rs[0-9]*"'
        self.parser.parseString(s)

        self.assertNotIn('dbSNP', self.parser.namespace_to_term)
        self.assertIn('dbSNP', self.parser.namespace_to_pattern)
        self.assertEqual(re.compile('rs[0-9]*'), self.parser.namespace_to_pattern['dbSNP'])

    def test_not_semantic_version(self):
        s = 'SET DOCUMENT Version = "1.0"'
        with self.assertRaises(VersionFormatWarning):
            self.parser.parseString(s)
