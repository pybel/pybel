# -*- coding: utf-8 -*-

import logging
import tempfile
import unittest
from pathlib import Path

import networkx as nx

from pybel import BELGraph
from pybel import to_cx_json, from_cx_json
from pybel.constants import GENE, CITATION, ANNOTATIONS, EVIDENCE
from pybel.io import to_json_dict, from_json_dict, to_bytes, from_bytes, to_graphml, from_path, from_url, to_cx_jsons, \
    from_cx_jsons
from pybel.parser import BelParser
from pybel.parser.parse_exceptions import *
from pybel.utils import hash_tuple
from tests.constants import BelReconstitutionMixin, test_bel_simple, TestTokenParserBase, SET_CITATION_TEST, \
    test_citation_dict, test_set_evidence, mock_bel_resources, test_bel_thorough, test_bel_slushy, test_evidence_text

logging.getLogger('requests').setLevel(logging.WARNING)


def do_remapping(G, H):
    """Remaps nodes to use the reconsitution tests
    
    :param BELGraph G: The original bel graph 
    :param BELGraph H: The reconsituted BEL graph from CX input/output
    """
    node_mapping = dict(enumerate(sorted(G.nodes_iter(), key=hash_tuple)))
    nx.relabel.relabel_nodes(H, node_mapping, copy=False)


class TestThoroughIo(BelReconstitutionMixin):
    @classmethod
    def setUpClass(cls):
        @mock_bel_resources
        def help_build_graph(mock):
            graph = from_path(test_bel_thorough, allow_nested=True)
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

    def test_cx(self):
        reconstituted = from_cx_json(to_cx_json(self.graph))

        do_remapping(self.graph, reconstituted)

        self.bel_thorough_reconstituted(
            reconstituted,
            check_warnings=False,
            check_provenance=False
        )

    def test_cxs(self):
        reconstituted = from_cx_jsons(to_cx_jsons(self.graph))

        do_remapping(self.graph, reconstituted)

        self.bel_thorough_reconstituted(
            reconstituted,
            check_warnings=False,
            check_provenance=False
        )


class TestSlushyIo(BelReconstitutionMixin):
    @classmethod
    def setUpClass(cls):
        @mock_bel_resources
        def help_build_graph(mock):
            graph = from_path(test_bel_slushy)
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
        g_bytes = to_bytes(self.graph)
        from_bytes(g_bytes)

    def test_cx(self):
        reconstituted = from_cx_json(to_cx_json(self.graph))

        do_remapping(self.graph, reconstituted)

        self.bel_slushy_reconstituted(reconstituted)

    def test_cxs(self):
        reconstituted = from_cx_jsons(to_cx_jsons(self.graph))

        do_remapping(self.graph, reconstituted)

        self.bel_slushy_reconstituted(reconstituted)


class TestSimpleIo(BelReconstitutionMixin):
    @mock_bel_resources
    def test_from_fileUrl(self, mock_get):
        g = from_url(Path(test_bel_simple).as_uri())
        self.bel_simple_reconstituted(g)

    def test_cx(self):
        """Tests the CX input/output on test_bel.bel"""
        graph = from_path(test_bel_simple)
        self.bel_simple_reconstituted(graph)

        reconstituted = from_cx_json(to_cx_json(graph))
        do_remapping(graph, reconstituted)

        self.bel_simple_reconstituted(reconstituted)


class TestRegex(unittest.TestCase):
    def setUp(self):
        self.graph = BELGraph()
        self.parser = BelParser(self.graph, namespace_dict={}, namespace_regex={'dbSNP': 'rs[0-9]*'})

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
        self.parser = BelParser(self.graph, namespace_dict=self.namespaces, annotation_dict=self.annotations)

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
        self.parser = BelParser(self.graph, namespace_dict=self.namespaces, allow_naked_names=True)
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
