# -*- coding: utf-8 -*-

import logging
import unittest
from pathlib import Path

import pybel
from pybel.constants import GENE, CITATION, ANNOTATIONS, EVIDENCE
from pybel.parser import BelParser
from pybel.parser.parse_exceptions import *
from tests import constants
from tests.constants import BelReconstitutionMixin, test_bel, TestTokenParserBase, SET_CITATION_TEST, \
    test_citation_dict, test_set_evidence, mock_bel_resources, test_bel_thorough, test_bel_slushy, test_evidence_text

logging.getLogger('requests').setLevel(logging.WARNING)


class TestImport(BelReconstitutionMixin, unittest.TestCase):
    @mock_bel_resources
    def test_bytes_io_test(self, mock_get):
        g = pybel.from_path(test_bel, complete_origin=True)
        self.bel_1_reconstituted(g)

        g_bytes = pybel.to_bytes(g)
        g_reloaded = pybel.from_bytes(g_bytes)
        self.bel_1_reconstituted(g_reloaded)

    @mock_bel_resources
    def test_bytes_io_slushy(self, mock_get):
        g = pybel.from_path(test_bel_slushy, complete_origin=True)
        g_bytes = pybel.to_bytes(g)
        pybel.from_bytes(g_bytes)

    @mock_bel_resources
    def test_bytes_io_thorough(self, mock_get):
        g = pybel.from_path(test_bel_thorough, complete_origin=False, allow_nested=True)
        self.bel_thorough_reconstituted(g)

        g_bytes = pybel.to_bytes(g)
        g_reloaded = pybel.from_bytes(g_bytes)
        self.bel_thorough_reconstituted(g_reloaded)

    @mock_bel_resources
    def test_from_fileUrl(self, mock_get):
        g = pybel.from_url(Path(test_bel).as_uri(), complete_origin=True)
        self.bel_1_reconstituted(g)

    @mock_bel_resources
    def test_slushy(self, mock_get):
        g = pybel.from_path(constants.test_bel_slushy)
        self.assertIsNotNone(g)

        expected_warnings = [
            (26, MissingAnnotationKeyWarning),
            (29, MissingAnnotationKeyWarning),
            (34, InvalidCitationException),
            (37, InvalidCitationType),
            (40, InvalidPubMedIdentifierWarning),
            (43, MissingCitationException),
            (48, MissingAnnotationKeyWarning),
            (51, MissingAnnotationKeyWarning),
            (54, MissingSupportWarning),
            (59, NakedNameWarning),
            (62, UndefinedNamespaceWarning),
            (65, MissingNamespaceNameWarning),
            (68, UndefinedAnnotationWarning),
            (71, MissingAnnotationKeyWarning),
            (74, IllegalAnnotationValueWarning),
            (77, MissingAnnotationRegexWarning),
            (80, MissingNamespaceRegexWarning),
            (83, MalformedTranslocationWarning),
            (86, PlaceholderAminoAcidWarning),
            (89, NestedRelationWarning),
            (92, InvalidFunctionSemantic),
            (95, Exception),
            (98, Exception),
        ]

        for (el, ew), (l, _, w, _) in zip(expected_warnings, g.warnings):
            self.assertEqual(el, l)
            self.assertIsInstance(w, ew, msg='Line: {}'.format(el))


class TestRegex(unittest.TestCase):
    def setUp(self):
        self.parser = BelParser(namespace_dicts={}, namespace_expressions={'dbSNP': 'rs[0-9]*'})

    def test_match(self):
        lines = [
            SET_CITATION_TEST,
            test_set_evidence,
            'g(dbSNP:rs10234) -- g(dbSNP:rs10235)'
        ]
        self.parser.parse_lines(lines)
        self.assertIn((GENE, 'dbSNP', 'rs10234'), self.parser.graph)
        self.assertIn((GENE, 'dbSNP', 'rs10235'), self.parser.graph)

    def test_no_match(self):
        lines = [
            SET_CITATION_TEST,
            test_set_evidence,
            'g(dbSNP:10234) -- g(dbSNP:rr10235)'
        ]

        with self.assertRaises(MissingNamespaceRegexWarning):
            self.parser.parse_lines(lines)


class TestFull(TestTokenParserBase):
    def setUp(self):
        self.namespaces = {
            'TESTNS': {
                "1": "GRP",
                "2": "GRP"
            }
        }

        self.annotations = {
            'TestAnnotation1': {'A', 'B', 'C'},
            'TestAnnotation2': {'X', 'Y', 'Z'},
            'TestAnnotation3': {'D', 'E', 'F'}
        }

        self.parser = BelParser(namespace_dicts=self.namespaces, annotation_dicts=self.annotations)

    def test_no_add_duplicates(self):
        s = 'r(TESTNS:1) -> r(TESTNS:2)'

        statements = [
            SET_CITATION_TEST,
            test_set_evidence,
            s
        ]

        self.parser.complete_origin = True

        self.parser.parse_lines(statements)
        self.assertEqual(4, self.parser.graph.number_of_nodes())

        self.parser.parseString(s)
        self.assertEqual(4, self.parser.graph.number_of_nodes())

    def test_semantic_failure(self):
        statement = "bp(TESTNS:1) -- p(TESTNS:2)"
        with self.assertRaises(InvalidFunctionSemantic):
            self.parser.parseString(statement)

    def test_lenient_semantic_no_failure(self):
        statements = [
            SET_CITATION_TEST,
            test_set_evidence,
            "bp(ABASD) -- p(ABASF)"
        ]

        self.parser = BelParser(namespace_dicts=self.namespaces, allow_naked_names=True)
        self.parser.parse_lines(statements)

    def test_missing_citation(self):
        statements = [
            test_set_evidence,
            'SET TestAnnotation1 = "A"',
            'SET TestAnnotation2 = "X"',
            'g(TESTNS:1) -> g(TESTNS:2)'
        ]

        with self.assertRaises(MissingCitationException):
            self.parser.parse_lines(statements)

    def test_annotations(self):
        statements = [
            SET_CITATION_TEST,
            test_set_evidence,
            'SET TestAnnotation1 = "A"',
            'SET TestAnnotation2 = "X"',
            'g(TESTNS:1) -> g(TESTNS:2)'
        ]
        self.parser.parse_lines(statements)

        test_node_1 = GENE, 'TESTNS', '1'
        test_node_2 = GENE, 'TESTNS', '2'

        self.assertEqual(2, self.parser.graph.number_of_nodes())
        self.assertHasNode(test_node_1)
        self.assertHasNode(test_node_2)

        self.assertEqual(1, self.parser.graph.number_of_edges())

        kwargs = {
            ANNOTATIONS: {
                'TestAnnotation1': 'A',
                'TestAnnotation2': 'X',
            },
            EVIDENCE: test_evidence_text,
            CITATION: test_citation_dict
        }
        self.assertHasEdge(test_node_1, test_node_2, **kwargs)

    def test_annotations_withList(self):
        statements = [
            SET_CITATION_TEST,
            test_set_evidence,
            'SET TestAnnotation1 = {"A","B"}',
            'SET TestAnnotation2 = "X"',
            'g(TESTNS:1) -> g(TESTNS:2)'
        ]
        self.parser.parse_lines(statements)

        test_node_1 = GENE, 'TESTNS', '1'
        test_node_2 = GENE, 'TESTNS', '2'

        self.assertEqual(2, self.parser.graph.number_of_nodes())
        self.assertHasNode(test_node_1)
        self.assertHasNode(test_node_2)

        self.assertEqual(2, self.parser.graph.number_of_edges())
        kwargs = {ANNOTATIONS: {'TestAnnotation1': 'A', 'TestAnnotation2': 'X'}, CITATION: test_citation_dict}
        self.assertHasEdge(test_node_1, test_node_2, **kwargs)
        kwargs = {ANNOTATIONS: {'TestAnnotation1': 'B', 'TestAnnotation2': 'X'}, CITATION: test_citation_dict}
        self.assertHasEdge(test_node_1, test_node_2, **kwargs)

    def test_annotations_withMultiList(self):
        statements = [
            SET_CITATION_TEST,
            test_set_evidence,
            'SET TestAnnotation1 = {"A","B"}',
            'SET TestAnnotation2 = "X"',
            'SET TestAnnotation3 = {"D","E"}',
            'g(TESTNS:1) -> g(TESTNS:2)'
        ]
        self.parser.parse_lines(statements)

        test_node_1 = GENE, 'TESTNS', '1'
        test_node_2 = GENE, 'TESTNS', '2'

        self.assertEqual(2, self.parser.graph.number_of_nodes())
        self.assertHasNode(test_node_1)
        self.assertHasNode(test_node_2)

        self.assertEqual(4, self.parser.graph.number_of_edges())

        kwargs = {
            ANNOTATIONS: {
                'TestAnnotation1': 'A',
                'TestAnnotation2': 'X',
                'TestAnnotation3': 'D'
            },
            CITATION: test_citation_dict
        }
        self.assertHasEdge(test_node_1, test_node_2, **kwargs)

        kwargs = {
            ANNOTATIONS: {
                'TestAnnotation1': 'A',
                'TestAnnotation2': 'X',
                'TestAnnotation3': 'E'
            },
            CITATION: test_citation_dict
        }
        self.assertHasEdge(test_node_1, test_node_2, **kwargs)

        kwargs = {
            ANNOTATIONS: {
                'TestAnnotation1': 'B',
                'TestAnnotation2': 'X',
                'TestAnnotation3': 'D'
            },
            CITATION: test_citation_dict
        }
        self.assertHasEdge(test_node_1, test_node_2, **kwargs)

        kwargs = {
            ANNOTATIONS: {
                'TestAnnotation1': 'B',
                'TestAnnotation2': 'X',
                'TestAnnotation3': 'E'
            },
            CITATION: test_citation_dict
        }
        self.assertHasEdge(test_node_1, test_node_2, **kwargs)
