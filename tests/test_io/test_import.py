# -*- coding: utf-8 -*-

"""Tests for input and output."""

import logging
import os
import tempfile
import unittest
from pathlib import Path

from six import BytesIO, StringIO

from pybel import (
    BELGraph, from_bytes, from_json, from_json_file, from_jsons, from_lines, from_path, from_pickle, from_url,
    to_bel_lines, to_bytes, to_csv, to_graphml, to_gsea, to_json, to_json_file, to_jsons, to_pickle, to_sif,
)
from pybel.constants import (
    ANNOTATIONS, CITATION, DECREASES, DIRECTLY_DECREASES, EVIDENCE, GENE, GRAPH_PYBEL_VERSION, INCREASES,
    PYBEL_MINIMUM_IMPORT_VERSION, RELATION,
)
from pybel.dsl import gene
from pybel.examples import sialic_acid_graph
from pybel.io.exc import ImportVersionWarning, import_version_message_fmt
from pybel.parser import BelParser
from pybel.parser.exc import InvalidFunctionSemantic, MissingCitationException, MissingNamespaceRegexWarning
from pybel.struct.summary import get_syntax_errors
from pybel.testing.cases import TemporaryCacheClsMixin
from pybel.testing.constants import (
    test_bel_isolated, test_bel_misordered, test_bel_simple, test_bel_slushy, test_bel_thorough,
)
from pybel.testing.mocks import mock_bel_resources
from tests.constants import (
    AKT1, BelReconstitutionMixin, CASP8, EGFR, FADD, TestTokenParserBase, citation_1, evidence_1, test_citation_dict,
    test_evidence_text, test_set_evidence,
)

logging.getLogger('requests').setLevel(logging.WARNING)
log = logging.getLogger(__name__)

testan1 = '1'


class TestExampleInterchange(unittest.TestCase):
    """Test round-trip interchange of the sialic acid graph example."""

    def help_test_equal(self, graph):
        """Check that a graph is equal to the sialic acid graph example.

        :type graph: pybel.BELGraph
        """
        self.assertEqual(set(sialic_acid_graph), set(graph))
        self.assertEqual(set(sialic_acid_graph.edges()), set(graph.edges()))

    def test_example_bytes(self):
        """Test the round-trip through bytes."""
        graph_bytes = to_bytes(sialic_acid_graph)
        graph = from_bytes(graph_bytes)
        self.help_test_equal(graph)

    def test_example_pickle(self):
        """Test the round-trip through a pickle."""
        bio = BytesIO()
        to_pickle(sialic_acid_graph, bio)
        bio.seek(0)
        graph = from_pickle(bio)
        self.help_test_equal(graph)

    def test_thorough_json(self):
        """Test the round-trip through node-link JSON."""
        graph_json_dict = to_json(sialic_acid_graph)
        graph = from_json(graph_json_dict)
        self.help_test_equal(graph)

    def test_thorough_jsons(self):
        """Test the round-trip through a node-link JSON string."""
        graph_json_str = to_jsons(sialic_acid_graph)
        graph = from_jsons(graph_json_str)
        self.help_test_equal(graph)

    def test_thorough_json_file(self):
        """Test the round-trip through a node-link JSON file."""
        sio = StringIO()
        to_json_file(sialic_acid_graph, sio)
        sio.seek(0)
        graph = from_json_file(sio)
        self.help_test_equal(graph)


class TestInterchange(TemporaryCacheClsMixin, BelReconstitutionMixin):
    @classmethod
    def setUpClass(cls):
        """Set up this class with several pre-loaded BEL graphs."""
        super(TestInterchange, cls).setUpClass()

        with mock_bel_resources:
            cls.thorough_graph = from_path(test_bel_thorough, manager=cls.manager, allow_nested=True)
            cls.slushy_graph = from_path(test_bel_slushy, manager=cls.manager)
            cls.simple_graph = from_url(Path(test_bel_simple).as_uri(), manager=cls.manager)
            cls.isolated_graph = from_path(test_bel_isolated, manager=cls.manager)
            cls.misordered_graph = from_path(test_bel_misordered, manager=cls.manager, citation_clearing=False)

    def test_thorough_path(self):
        self.bel_thorough_reconstituted(self.thorough_graph)

    def test_thorough_bytes(self):
        graph_bytes = to_bytes(self.thorough_graph)
        graph = from_bytes(graph_bytes)
        self.bel_thorough_reconstituted(graph)

    def test_thorough_pickle(self):
        bio = BytesIO()
        to_pickle(self.thorough_graph, bio)
        bio.seek(0)
        graph = from_pickle(bio)
        self.bel_thorough_reconstituted(graph)

    def test_thorough_json(self):
        graph_json_dict = to_json(self.thorough_graph)
        graph = from_json(graph_json_dict)
        self.bel_thorough_reconstituted(graph)

    def test_thorough_jsons(self):
        graph_json_str = to_jsons(self.thorough_graph)
        graph = from_jsons(graph_json_str)
        self.bel_thorough_reconstituted(graph)

    def test_thorough_json_file(self):
        sio = StringIO()
        to_json_file(self.thorough_graph, sio)
        sio.seek(0)
        graph = from_json_file(sio)
        self.bel_thorough_reconstituted(graph)

    def test_thorough_graphml(self):
        handle, path = tempfile.mkstemp()

        with open(path, 'wb') as f:
            to_graphml(self.thorough_graph, f)

        os.close(handle)
        os.remove(path)

    def test_thorough_csv(self):
        handle, path = tempfile.mkstemp()

        with open(path, 'w') as f:
            to_csv(self.thorough_graph, f)

        os.close(handle)
        os.remove(path)

    def test_thorough_sif(self):
        handle, path = tempfile.mkstemp()

        with open(path, 'w') as f:
            to_sif(self.thorough_graph, f)

        os.close(handle)
        os.remove(path)

    def test_thorough_gsea(self):
        handle, path = tempfile.mkstemp()

        with open(path, 'w') as f:
            to_gsea(self.thorough_graph, f)

        os.close(handle)
        os.remove(path)

    def test_thorough_upgrade(self):
        lines = to_bel_lines(self.thorough_graph)
        reconstituted = from_lines(lines, manager=self.manager)
        self.bel_thorough_reconstituted(reconstituted, check_citation_name=False)

    def test_slushy(self):
        self.bel_slushy_reconstituted(self.slushy_graph)

    def test_slushy_bytes(self):
        graph_bytes = to_bytes(self.slushy_graph)
        graph = from_bytes(graph_bytes)
        self.bel_slushy_reconstituted(graph)

    def test_slushy_syntax_errors(self):
        syntax_errors = get_syntax_errors(self.slushy_graph)
        self.assertEqual(1, len(syntax_errors))
        self.assertEqual(98, syntax_errors[0][0])

    def test_slushy_json(self):
        graph_json = to_json(self.slushy_graph)
        graph = from_json(graph_json)
        self.bel_slushy_reconstituted(graph)

    def test_slushy_graphml(self):
        handle, path = tempfile.mkstemp()

        with open(path, 'wb') as f:
            to_graphml(self.slushy_graph, f)

        os.close(handle)
        os.remove(path)

    def test_simple_compile(self):
        self.bel_simple_reconstituted(self.simple_graph)

    def test_isolated_compile(self):
        self.bel_isolated_reconstituted(self.isolated_graph)

    def test_isolated_upgrade(self):
        lines = to_bel_lines(self.isolated_graph)

        with mock_bel_resources:
            reconstituted = from_lines(lines, manager=self.manager)

        self.bel_isolated_reconstituted(reconstituted)

    def test_misordered_compile(self):
        """Test that non-citation clearing mode works."""
        self.assertEqual(4, self.misordered_graph.number_of_nodes())
        self.assertEqual(3, self.misordered_graph.number_of_edges())

        e1 = {
            RELATION: INCREASES,
            CITATION: citation_1,
            EVIDENCE: evidence_1,
            ANNOTATIONS: {
                'TESTAN1': {testan1: True}
            }
        }
        self.assert_has_edge(self.misordered_graph, AKT1, EGFR, **e1)

        e2 = {
            RELATION: DECREASES,
            CITATION: citation_1,
            EVIDENCE: evidence_1,
            ANNOTATIONS: {
                'TESTAN1': {testan1: True}
            }
        }
        self.assert_has_edge(self.misordered_graph, EGFR, FADD, **e2)

        e3 = {
            RELATION: DIRECTLY_DECREASES,
            CITATION: citation_1,
            EVIDENCE: evidence_1,
            ANNOTATIONS: {
                'TESTAN1': {testan1: True}
            }
        }
        self.assert_has_edge(self.misordered_graph, EGFR, CASP8, **e3)


namespaces = {
    'TESTNS': {
        "1": "GRP",
        "2": "GRP"
    }
}

annotations = {
    'TestAnnotation1': {'A', 'B', 'C'},
    'TestAnnotation2': {'X', 'Y', 'Z'},
    'TestAnnotation3': {'D', 'E', 'F'}
}


class TestFull(TestTokenParserBase):
    @classmethod
    def setUpClass(cls):
        cls.graph = BELGraph()
        cls.parser = BelParser(
            cls.graph,
            namespace_dict=namespaces,
            annotation_dict=annotations,
            namespace_regex={'dbSNP': 'rs[0-9]*'}
        )

    def test_regex_match(self):
        line = 'g(dbSNP:rs10234) -- g(dbSNP:rs10235)'
        self.add_default_provenance()
        self.parser.parseString(line)
        self.assertIn((GENE, 'dbSNP', 'rs10234'), self.parser.graph)
        self.assertIn((GENE, 'dbSNP', 'rs10235'), self.parser.graph)

    def test_regex_mismatch(self):
        line = 'g(dbSNP:10234) -- g(dbSNP:rr10235)'

        with self.assertRaises(MissingNamespaceRegexWarning):
            self.parser.parseString(line)

    def test_semantic_failure(self):
        statement = "bp(TESTNS:1) -- p(TESTNS:2)"
        with self.assertRaises(InvalidFunctionSemantic):
            self.parser.parseString(statement)

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
        self.add_default_provenance()

        statements = [
            'SET TestAnnotation1 = "A"',
            'SET TestAnnotation2 = "X"',
            'g(TESTNS:1) -> g(TESTNS:2)'
        ]

        self.parser.parse_lines(statements)

        test_node_1_dict = gene(namespace='TESTNS', name='1')
        test_node_2_dict = gene(namespace='TESTNS', name='2')

        self.assertEqual(2, self.graph.number_of_nodes())
        self.assertTrue(self.graph.has_node_with_data(test_node_1_dict))
        self.assertTrue(self.graph.has_node_with_data(test_node_2_dict))

        test_node_1 = test_node_1_dict.as_tuple()
        test_node_2 = test_node_2_dict.as_tuple()

        self.assertEqual(1, self.parser.graph.number_of_edges())

        kwargs = {
            ANNOTATIONS: {
                'TestAnnotation1': {'A': True},
                'TestAnnotation2': {'X': True},
            },
            EVIDENCE: test_evidence_text,
            CITATION: test_citation_dict
        }
        self.assert_has_edge(test_node_1, test_node_2, **kwargs)

    def test_annotations_with_list(self):
        self.add_default_provenance()

        statements = [
            'SET TestAnnotation1 = {"A","B"}',
            'SET TestAnnotation2 = "X"',
            'g(TESTNS:1) -> g(TESTNS:2)'
        ]
        self.parser.parse_lines(statements)

        test_node_1_dict = gene(namespace='TESTNS', name='1')
        test_node_2_dict = gene(namespace='TESTNS', name='2')

        self.assertEqual(2, self.parser.graph.number_of_nodes())
        self.assertTrue(self.parser.graph.has_node_with_data(test_node_1_dict))
        self.assertTrue(self.parser.graph.has_node_with_data(test_node_2_dict))

        test_node_1 = test_node_1_dict.as_tuple()
        test_node_2 = test_node_2_dict.as_tuple()

        self.assertEqual(1, self.parser.graph.number_of_edges())

        kwargs = {
            ANNOTATIONS: {
                'TestAnnotation1': {'A': True, 'B': True},
                'TestAnnotation2': {'X': True}
            },
            CITATION: test_citation_dict
        }
        self.assert_has_edge(test_node_1, test_node_2, **kwargs)

    def test_annotations_with_multilist(self):
        self.add_default_provenance()

        statements = [
            'SET TestAnnotation1 = {"A","B"}',
            'SET TestAnnotation2 = "X"',
            'SET TestAnnotation3 = {"D","E"}',
            'g(TESTNS:1) -> g(TESTNS:2)'
        ]
        self.parser.parse_lines(statements)

        test_node_1_dict = gene(namespace='TESTNS', name='1')
        test_node_2_dict = gene(namespace='TESTNS', name='2')

        test_node_1 = test_node_1_dict.as_tuple()
        test_node_2 = test_node_2_dict.as_tuple()

        self.assertEqual(2, self.parser.graph.number_of_nodes())
        self.assertTrue(self.parser.graph.has_node_with_data(test_node_1_dict))
        self.assertTrue(self.parser.graph.has_node_with_data(test_node_2_dict))

        self.assertEqual(1, self.parser.graph.number_of_edges())

        kwargs = {
            ANNOTATIONS: {
                'TestAnnotation1': {'A': True, 'B': True},
                'TestAnnotation2': {'X': True},
                'TestAnnotation3': {'D': True, 'E': True}
            },
            CITATION: test_citation_dict
        }
        self.assert_has_edge(test_node_1, test_node_2, **kwargs)


class TestRandom(unittest.TestCase):
    def test_import_warning(self):
        """Tests an error is thrown when the version is set wrong"""
        graph = BELGraph()

        # Much with stuff that would normally be set
        graph.graph[GRAPH_PYBEL_VERSION] = '0.0.0'

        graph_bytes = to_bytes(graph)

        with self.assertRaises(ImportVersionWarning) as cm:
            from_bytes(graph_bytes)

            self.assertEqual(
                import_version_message_fmt.format('0.0.0', PYBEL_MINIMUM_IMPORT_VERSION),
                str(cm.exception)
            )


if __name__ == '__main__':
    unittest.main()
