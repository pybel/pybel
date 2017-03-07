# -*- coding: utf-8 -*-

import logging
import tempfile
import unittest
from pathlib import Path

import pybel
from pybel import BELGraph
from pybel import to_bytes, from_bytes, to_graphml
from pybel.constants import GENE, CITATION, ANNOTATIONS, EVIDENCE
from pybel.io import to_json_dict, from_json_dict
from pybel.parser import BelParser
from pybel.parser.parse_exceptions import *
from tests.constants import BelReconstitutionMixin, test_bel_simple, TestTokenParserBase, SET_CITATION_TEST, \
    test_citation_dict, test_set_evidence, mock_bel_resources, test_bel_thorough, test_bel_slushy, test_evidence_text

logging.getLogger('requests').setLevel(logging.WARNING)


class TestThoroughIo(BelReconstitutionMixin):
    @classmethod
    def setUpClass(cls):
        @mock_bel_resources
        def help_build_graph(mock):
            graph = pybel.from_path(test_bel_thorough, complete_origin=False, allow_nested=True)
            return graph

        cls.graph = help_build_graph()

    def test_path(self):
        self.bel_thorough_reconstituted(self.graph)

    def test_bytes(self):
        graph_bytes = to_bytes(self.graph)
        graph = from_bytes(graph_bytes)
        self.bel_thorough_reconstituted(graph)

    def test_json(self):
        graph_json = to_json_dict(self.graph)
        graph = from_json_dict(graph_json)
        self.bel_thorough_reconstituted(graph)

    def test_graphml(self):
        handle, path = tempfile.mkstemp()

        with open(path, 'wb') as f:
            to_graphml(self.graph, f)


class TestSlushyIo(BelReconstitutionMixin):
    @classmethod
    def setUpClass(cls):
        @mock_bel_resources
        def help_build_graph(mock):
            graph = pybel.from_path(test_bel_slushy, complete_origin=True)
            return graph

        cls.graph = help_build_graph()

    def test_slushy(self):
        self.bel_slushy_reconstituted(self.graph)

    def test_bytes(self):
        graph_bytes = to_bytes(self.graph)
        graph = from_bytes(graph_bytes)
        self.bel_slushy_reconstituted(graph)

    def test_json(self):
        graph_json = to_json_dict(self.graph)
        graph = from_json_dict(graph_json)
        self.bel_slushy_reconstituted(graph)

    def test_graphml(self):
        handle, path = tempfile.mkstemp()

        with open(path, 'wb') as f:
            to_graphml(self.graph, f)

    def test_bytes_io_slushy(self):
        g_bytes = pybel.to_bytes(self.graph)
        pybel.from_bytes(g_bytes)


class TestImport(BelReconstitutionMixin, unittest.TestCase):
    @mock_bel_resources
    def test_from_fileUrl(self, mock_get):
        g = pybel.from_url(Path(test_bel_simple).as_uri())
        self.bel_simple_reconstituted(g)


class TestRegex(unittest.TestCase):
    def setUp(self):
        self.graph = BELGraph()
        self.parser = BelParser(self.graph, namespace_dicts={}, namespace_expressions={'dbSNP': 'rs[0-9]*'})

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

        self.graph = BELGraph()
        self.parser = BelParser(self.graph, namespace_dicts=self.namespaces, annotation_dicts=self.annotations)

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
        self.graph = BELGraph()
        self.parser = BelParser(self.graph, namespace_dicts=self.namespaces, allow_naked_names=True)
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
