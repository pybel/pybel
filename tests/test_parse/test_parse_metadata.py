# -*- coding: utf-8 -*-

"""Test parsing metadata from a BEL script."""

import logging
import os
import re
import unittest
from pathlib import Path

from bel_resources.constants import ANNOTATION_URL_FMT, NAMESPACE_URL_FMT

from pybel.exceptions import (
    InvalidMetadataException,
    RedefinedAnnotationError,
    RedefinedNamespaceError,
    VersionFormatWarning,
)
from pybel.parser import MetadataParser
from pybel.resources import HGNC_URL
from pybel.testing.cases import FleetingTemporaryCacheMixin
from pybel.testing.constants import test_an_1, test_ns_1
from pybel.testing.mocks import mock_bel_resources
from tests.constants import (
    HGNC_KEYWORD,
    MESH_DISEASES_KEYWORD,
    MESH_DISEASES_URL,
    help_check_hgnc,
)

logging.getLogger("requests").setLevel(logging.WARNING)

LOCAL_TEST_PATH = os.path.expanduser("~/dev/pybel/src/pybel/testing/resources/belns/hgnc-names.belns")


class TestParseMetadata(FleetingTemporaryCacheMixin):
    def setUp(self):
        super(TestParseMetadata, self).setUp()
        self.parser = MetadataParser(manager=self.manager)

    def _help_test_local_annotation(self, annotation: str) -> None:
        """Check that the annotation is defined locally."""
        self.assertTrue(self.parser.has_annotation(annotation))
        self.assertNotIn(annotation, self.parser.annotation_to_term)
        self.assertFalse(self.parser.has_enumerated_annotation(annotation))
        self.assertNotIn(annotation, self.parser.annotation_to_pattern)
        self.assertFalse(self.parser.has_regex_annotation(annotation))
        self.assertIn(annotation, self.parser.annotation_to_local)
        self.assertTrue(self.parser.has_local_annotation(annotation))

    @mock_bel_resources
    def test_namespace_name_persistience(self, mock_get):
        """Test that a namespace defined by a URL can't be overwritten by a definition by another URL."""
        s = NAMESPACE_URL_FMT.format(HGNC_KEYWORD, HGNC_URL)
        self.parser.parseString(s)
        self.parser.ensure_resources()
        help_check_hgnc(self, self.parser.namespace_to_term_to_encoding)

        s = NAMESPACE_URL_FMT.format(HGNC_KEYWORD, "XXXXX")
        with self.assertRaises(RedefinedNamespaceError):
            self.parser.parseString(s)

        help_check_hgnc(self, self.parser.namespace_to_term_to_encoding)

    @mock_bel_resources
    def test_annotation_name_persistience_1(self, mock_get):
        """Test that an annotation defined by a URL can't be overwritten by a definition by a list."""
        s = ANNOTATION_URL_FMT.format(MESH_DISEASES_KEYWORD, MESH_DISEASES_URL)
        self.parser.parseString(s)
        self.parser.ensure_resources()

        self.assertIn(MESH_DISEASES_KEYWORD, self.parser.annotation_to_term)

        s = 'DEFINE ANNOTATION {} AS LIST {{"A","B","C"}}'.format(MESH_DISEASES_KEYWORD)
        with self.assertRaises(RedefinedAnnotationError):
            self.parser.parseString(s)

        self.assertIn(MESH_DISEASES_KEYWORD, self.parser.annotation_to_term)
        self.assertNotIn("A", self.parser.annotation_to_term[MESH_DISEASES_KEYWORD])
        self.assertIn(
            "46, XX Disorders of Sex Development",
            self.parser.annotation_to_term[MESH_DISEASES_KEYWORD],
        )

    def test_annotation_name_persistience_2(self):
        """Tests that an annotation defined by a list can't be overwritten by a definition by URL"""
        s = 'DEFINE ANNOTATION TextLocation AS LIST {"Abstract","Results","Legend","Review"}'
        self.parser.parseString(s)
        self._help_test_local_annotation("TextLocation")

        s = ANNOTATION_URL_FMT.format("TextLocation", MESH_DISEASES_URL)
        with self.assertRaises(RedefinedAnnotationError):
            self.parser.parseString(s)

        self._help_test_local_annotation("TextLocation")
        self.assertIn("Abstract", self.parser.annotation_to_local["TextLocation"])

    def test_underscore(self):
        """Tests that an underscore is a valid character in an annotation name"""
        s = 'DEFINE ANNOTATION Text_Location AS LIST {"Abstract","Results","Legend","Review"}'
        self.parser.parseString(s)
        self._help_test_local_annotation("Text_Location")

    @mock_bel_resources
    def test_control_compound(self, mock_get):
        text_location = "TextLocation"
        lines = [
            ANNOTATION_URL_FMT.format(MESH_DISEASES_KEYWORD, MESH_DISEASES_URL),
            NAMESPACE_URL_FMT.format(HGNC_KEYWORD, HGNC_URL),
            'DEFINE ANNOTATION TextLocation AS LIST {"Abstract","Results","Legend","Review"}',
        ]
        self.parser.parse_lines(lines)
        self.parser.ensure_resources()

        self.assertIn(MESH_DISEASES_KEYWORD, self.parser.annotation_to_term)
        self.assertIn(HGNC_KEYWORD, self.parser.namespace_to_term_to_encoding)
        self._help_test_local_annotation(text_location)

    @unittest.skipUnless(os.path.exists(LOCAL_TEST_PATH), "Need local files to test local files")
    def test_squiggly_filepath(self):
        line = NAMESPACE_URL_FMT.format(HGNC_KEYWORD, LOCAL_TEST_PATH)
        self.parser.parseString(line)
        help_check_hgnc(self, self.parser.namespace_to_term_to_encoding)

    def test_document_metadata_exception(self):
        s = 'SET DOCUMENT InvalidKey = "nope"'
        with self.assertRaises(InvalidMetadataException):
            self.parser.parseString(s)

    def test_parse_document(self):
        s = '''SET DOCUMENT Name = "Alzheimer's Disease Model"'''

        self.parser.parseString(s)

        self.assertIn("name", self.parser.document_metadata)
        self.assertEqual("Alzheimer's Disease Model", self.parser.document_metadata["name"])

        # Check nothing bad happens
        # with self.assertLogs('pybel', level='WARNING'):
        self.parser.parseString(s)

    @mock_bel_resources
    def test_parse_namespace_url_file(self, mock):
        """Tests parsing a namespace by file URL"""
        s = NAMESPACE_URL_FMT.format("TESTNS1", test_ns_1)
        self.parser.parseString(s)
        self.parser.ensure_resources()

        expected_values = {
            "TestValue1": {"O"},
            "TestValue2": {"O"},
            "TestValue3": {"O"},
            "TestValue4": {"O"},
            "TestValue5": {"O"},
        }

        self.assertIn("TESTNS1", self.parser.namespace_to_term_to_encoding)

        for k, values in expected_values.items():
            k = (None, k)
            self.assertIn(k, self.parser.namespace_to_term_to_encoding["TESTNS1"])
            self.assertEqual(
                set(values),
                set(self.parser.namespace_to_term_to_encoding["TESTNS1"][k]),
            )

    def test_parse_annotation_url_file(self):
        """Tests parsing an annotation by file URL"""
        keyword = "TESTAN1"
        url = Path(test_an_1).as_uri()
        line = ANNOTATION_URL_FMT.format(keyword, url)
        self.parser.parseString(line)
        self.parser.ensure_resources()

        expected_values = {
            "TestAnnot1": "O",
            "TestAnnot2": "O",
            "TestAnnot3": "O",
            "TestAnnot4": "O",
            "TestAnnot5": "O",
        }

        annotation = self.parser.manager.get_namespace_by_url(url)
        self.assertIsNotNone(annotation)
        self.assertEqual(set(expected_values), {e.name for e in annotation.entries})

    def test_parse_annotation_pattern(self):
        s = r'DEFINE ANNOTATION Test AS PATTERN "\w+"'
        self.parser.parseString(s)

        self.assertNotIn("Test", self.parser.annotation_to_term)
        self.assertIn("Test", self.parser.annotation_to_pattern)
        self.assertEqual(re.compile(r"\w+"), self.parser.annotation_to_pattern["Test"])

    def test_define_namespace_regex(self):
        for s, namespace, regex in [
            (
                'DEFINE NAMESPACE dbSNP AS PATTERN "rs[0-9]*"',
                "dbSNP",
                re.compile(r"rs[0-9]*"),
            ),
            ('DEFINE NAMESPACE ec-code AS PATTERN ".*"', "ec-code", re.compile(r".*")),
        ]:
            with self.subTest(namespace=namespace):
                self.parser.parseString(s)
                self.assertNotIn(namespace, self.parser.namespace_to_term_to_encoding)
                self.assertIn(namespace, self.parser.namespace_to_pattern)
                self.assertEqual(regex, self.parser.namespace_to_pattern[namespace])

    def test_not_semantic_version(self):
        s = 'SET DOCUMENT Version = "1.0"'
        with self.assertRaises(VersionFormatWarning):
            self.parser.parseString(s)
