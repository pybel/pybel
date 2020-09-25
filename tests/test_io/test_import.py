# -*- coding: utf-8 -*-

"""Tests for input and output."""

import logging
import os
import re
import tempfile
import unittest
from io import BytesIO, StringIO
from pathlib import Path

import pybel
from pybel import (
    BELGraph, from_bel_script, from_bel_script_url, from_bytes, from_nodelink, from_nodelink_file, from_pickle,
    to_bel_script_lines, to_bytes, to_csv, to_graphml, to_gsea, to_nodelink, to_nodelink_file, to_pickle, to_sif,
)
from pybel.config import PYBEL_MINIMUM_IMPORT_VERSION
from pybel.constants import (
    ANNOTATIONS, CITATION, DECREASES, DIRECTLY_DECREASES, EVIDENCE, GRAPH_ANNOTATION_MIRIAM, GRAPH_PYBEL_VERSION,
    INCREASES, RELATION,
)
from pybel.dsl import BaseEntity, Gene, Protein
from pybel.examples.sialic_acid_example import sialic_acid_graph
from pybel.exceptions import (
    BELSyntaxError, InvalidFunctionSemantic, MissingCitationException, MissingNamespaceRegexWarning,
)
from pybel.io.exc import ImportVersionWarning, import_version_message_fmt
from pybel.io.line_utils import parse_lines
from pybel.io.nodelink import from_nodelink_jsons, to_nodelink_jsons
from pybel.language import Entity
from pybel.parser import BELParser
from pybel.struct.summary import get_syntax_errors
from pybel.testing.cases import TemporaryCacheClsMixin, TemporaryCacheMixin
from pybel.testing.constants import (
    test_bel_isolated, test_bel_misordered, test_bel_simple, test_bel_slushy, test_bel_thorough, test_bel_with_obo,
)
from pybel.testing.mocks import mock_bel_resources
from tests.constants import (
    BelReconstitutionMixin, TestTokenParserBase, akt1, casp8, citation_1, egfr, evidence_1, fadd, test_citation_dict,
    test_evidence_text, test_set_evidence,
)

logging.getLogger('requests').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

testan1 = '1'


class TestExampleInterchange(unittest.TestCase):
    """Test round-trip interchange of the sialic acid graph example."""

    def _help_test_equal(self, graph: BELGraph):
        """Check that a graph is equal to the sialic acid graph example."""
        for node in graph:
            self.assertIsInstance(node, BaseEntity)

        self.assertEqual(set(sialic_acid_graph), set(graph))
        self.assertEqual(set(sialic_acid_graph.edges()), set(graph.edges()))

        for node in sialic_acid_graph:
            if not isinstance(node, Protein):
                continue
            if node.namespace == 'HGNC' and node.name == 'CD33' and not node.variants:
                self.assertIsNotNone(node.xrefs)
                self.assertEqual(1, len(node.xrefs))

    def test_example_bytes(self):
        """Test the round-trip through bytes."""
        graph_bytes = to_bytes(sialic_acid_graph)
        graph = from_bytes(graph_bytes)
        self._help_test_equal(graph)

    def test_thorough_bytes_gz(self):
        """Test the round-trip through gzipped bytes."""
        graph_bytes = pybel.to_bytes_gz(sialic_acid_graph)
        graph = pybel.from_bytes_gz(graph_bytes)
        self._help_test_equal(graph)

    def test_example_pickle(self):
        """Test the round-trip through a pickle."""
        bio = BytesIO()
        to_pickle(sialic_acid_graph, bio)
        bio.seek(0)
        graph = from_pickle(bio)
        self._help_test_equal(graph)

    def test_example_pickle_gz(self):
        """Test the round-trip through a gzipped pickle."""
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'test.gz')
            pybel.to_pickle_gz(sialic_acid_graph, path)
            graph = pybel.from_pickle_gz(path)
        self._help_test_equal(graph)

    def test_thorough_json(self):
        """Test the round-trip through node-link JSON."""
        graph_json_dict = to_nodelink(sialic_acid_graph)
        graph = from_nodelink(graph_json_dict)
        self._help_test_equal(graph)

    def test_thorough_jsons(self):
        """Test the round-trip through a node-link JSON string."""
        graph_json_str = to_nodelink_jsons(sialic_acid_graph)
        graph = from_nodelink_jsons(graph_json_str)
        self._help_test_equal(graph)

    def test_thorough_json_file(self):
        """Test the round-trip through a node-link JSON file."""
        sio = StringIO()
        to_nodelink_file(sialic_acid_graph, sio)
        sio.seek(0)
        graph = from_nodelink_file(sio)
        self._help_test_equal(graph)

    def test_thorough_sbel(self):
        """Test the round-trip through SBEL."""
        s = pybel.to_sbel(sialic_acid_graph)
        graph = pybel.from_sbel(s)
        self._help_test_equal(graph)

    def test_thorough_sbel_file(self):
        """Test the round-trip through a SBEL file."""
        sio = StringIO()
        pybel.to_sbel_file(sialic_acid_graph, sio)
        sio.seek(0)
        graph = pybel.from_sbel_file(sio)
        self._help_test_equal(graph)

    def test_thorough_sbel_gzip_path(self):
        """Test round trip through a SBEL gzipped file."""
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'test.gzip')
            pybel.to_sbel_gz(sialic_acid_graph, path)
            graph = pybel.from_sbel_gz(path)
        self._help_test_equal(graph)


class TestInterchange(TemporaryCacheClsMixin, BelReconstitutionMixin):
    @classmethod
    def setUpClass(cls):
        """Set up this class with several pre-loaded BEL graphs."""
        super().setUpClass()

        with mock_bel_resources:
            cls.thorough_graph = from_bel_script(test_bel_thorough, manager=cls.manager, disallow_nested=False)
            cls.slushy_graph = from_bel_script(
                test_bel_slushy,
                manager=cls.manager,
                disallow_unqualified_translocations=True,
                disallow_nested=True,
            )
            cls.simple_graph = from_bel_script_url(Path(test_bel_simple).as_uri(), manager=cls.manager)
            cls.isolated_graph = from_bel_script(test_bel_isolated, manager=cls.manager)
            cls.misordered_graph = from_bel_script(test_bel_misordered, manager=cls.manager, citation_clearing=False)

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
        graph_json_dict = to_nodelink(self.thorough_graph)
        graph = from_nodelink(graph_json_dict)
        self.bel_thorough_reconstituted(graph)

    def test_thorough_jsons(self):
        graph_json_str = to_nodelink_jsons(self.thorough_graph)
        graph = from_nodelink_jsons(graph_json_str)
        self.bel_thorough_reconstituted(graph)

    def test_thorough_json_file(self):
        sio = StringIO()
        to_nodelink_file(self.thorough_graph, sio)
        sio.seek(0)
        graph = from_nodelink_file(sio)
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
        lines = to_bel_script_lines(self.thorough_graph, use_identifiers=True)
        reconstituted = BELGraph()
        parse_lines(reconstituted, lines, manager=self.manager)
        self.bel_thorough_reconstituted(reconstituted, check_citation_name=False, check_path=False)

    def test_slushy(self):
        self.bel_slushy_reconstituted(self.slushy_graph)

    def test_slushy_bytes(self):
        graph_bytes = to_bytes(self.slushy_graph)
        graph = from_bytes(graph_bytes)
        self.bel_slushy_reconstituted(graph)

    def test_slushy_syntax_errors(self):
        syntax_errors = get_syntax_errors(self.slushy_graph)
        for _, exc, _ in syntax_errors:
            self.assertIsInstance(exc, BELSyntaxError)
        self.assertEqual(1, len(syntax_errors))
        _, first_exc, _ = syntax_errors[0]
        self.assertEqual(98, first_exc.line_number)

    def test_slushy_json(self):
        graph_json = to_nodelink(self.slushy_graph)
        graph = from_nodelink(graph_json)
        self.bel_slushy_reconstituted(graph, check_warnings=False)

    def test_slushy_graphml(self):
        handle, path = tempfile.mkstemp()
        to_graphml(self.slushy_graph, path)
        os.close(handle)
        os.remove(path)

    def test_simple_compile(self):
        self.bel_simple_reconstituted(self.simple_graph)

    def test_isolated_compile(self):
        self.bel_isolated_reconstituted(self.isolated_graph)

    def test_isolated_upgrade(self):
        lines = to_bel_script_lines(self.isolated_graph)

        with mock_bel_resources:
            reconstituted = BELGraph()
            parse_lines(graph=reconstituted, lines=lines, manager=self.manager)

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
        self.assert_has_edge(self.misordered_graph, akt1, egfr, only=True, **e1)

        e2 = {
            RELATION: DECREASES,
            CITATION: citation_1,
            EVIDENCE: evidence_1,
            ANNOTATIONS: {
                'TESTAN1': {testan1: True}
            }
        }
        self.assert_has_edge(self.misordered_graph, egfr, fadd, only=True, **e2)

        e3 = {
            RELATION: DIRECTLY_DECREASES,
            CITATION: citation_1,
            EVIDENCE: evidence_1,
            ANNOTATIONS: {
                'TESTAN1': {testan1: True},
            },
        }
        self.assert_has_edge(self.misordered_graph, egfr, casp8, only=True, **e3)


namespace_to_term = {
    'TESTNS': {
        (None, "1"): "GRP",
        (None, "2"): "GRP",
    }
}

annotation_to_term = {
    'TestAnnotation1': {'A', 'B', 'C'},
    'TestAnnotation2': {'X', 'Y', 'Z'},
    'TestAnnotation3': {'D', 'E', 'F'},
}


class TestFull(TestTokenParserBase):
    @classmethod
    def setUpClass(cls):
        cls.parser = BELParser(
            graph=BELGraph(),  # gets overwritten in each test
            namespace_to_term_to_encoding=namespace_to_term,
            annotation_to_term=annotation_to_term,
            namespace_to_pattern={'dbSNP': re.compile('rs[0-9]*')},
        )

    def setUp(self):
        self.parser.clear()
        self.parser.graph = BELGraph()
        self.graph.annotation_list.update({
            'TestAnnotation1': {'A', 'B', 'C'},
            'TestAnnotation2': {'X', 'Y', 'Z'},
            'TestAnnotation3': {'D', 'E', 'F'},
        })
        self.parser.graph = self.graph
        self.assertIn(GRAPH_ANNOTATION_MIRIAM, self.graph.graph, msg=f'Graph metadata: {self.graph.graph}')

    def test_regex_match(self):
        line = 'g(dbSNP:rs10234) -- g(dbSNP:rs10235)'
        self.add_default_provenance()
        self.parser.parseString(line)
        self.assertIn(Gene('dbSNP', 'rs10234'), self.parser.graph)
        self.assertIn(Gene('dbSNP', 'rs10235'), self.parser.graph)

    def test_regex_mismatch(self):
        statement = 'g(dbSNP:10234) -- g(dbSNP:rr10235)'
        with self.assertRaises(MissingNamespaceRegexWarning):
            self.parser.parseString(statement)

    def test_semantic_failure(self):
        self.assertIsNotNone(self.parser.concept_parser.namespace_to_name_to_encoding)
        self.assertIn('TESTNS', self.parser.concept_parser.namespace_to_name_to_encoding)
        self.assertIn('1', self.parser.concept_parser.namespace_to_name_to_encoding['TESTNS'])
        self.assertIn('2', self.parser.concept_parser.namespace_to_name_to_encoding['TESTNS'])
        statement = "bp(TESTNS:1) -- p(TESTNS:2)"
        with self.assertRaises(InvalidFunctionSemantic):
            self.parser.parseString(statement)

    def test_missing_citation(self):
        statements = [
            test_set_evidence,
            'SET TestAnnotation1 = "A"',
            'SET TestAnnotation2 = "X"',
            'g(TESTNS:1) -> g(TESTNS:2)',
        ]

        with self.assertRaises(MissingCitationException):
            self.parser.parse_lines(statements)

    def test_annotations(self):
        self.add_default_provenance()

        statements = [
            'SET TestAnnotation1 = "A"',
            'SET TestAnnotation2 = "X"',
            'g(TESTNS:1) -> g(TESTNS:2)',
        ]

        self.parser.parse_lines(statements)

        self.assertEqual(2, len(self.parser.control_parser.annotations))
        self.assertIn('TestAnnotation1', self.parser.control_parser.annotations)
        self.assertIn('TestAnnotation2', self.parser.control_parser.annotations)

        test_node_1 = Gene(namespace='TESTNS', name='1')
        test_node_2 = Gene(namespace='TESTNS', name='2')

        self.assertEqual(2, self.graph.number_of_nodes())
        self.assertIn(test_node_1, self.graph)
        self.assertIn(test_node_2, self.graph)

        self.assertEqual(1, self.parser.graph.number_of_edges())

        kwargs = {
            RELATION: INCREASES,
            ANNOTATIONS: {
                'TestAnnotation1': {'A': True},
                'TestAnnotation2': {'X': True},
            },
            EVIDENCE: test_evidence_text,
            CITATION: test_citation_dict,
        }

        self.assert_has_edge(test_node_1, test_node_2, only=True, **kwargs)

    def test_annotations_with_list(self):
        self.assertIsNotNone(self.parser.graph)
        self.add_default_provenance()

        statements = [
            'SET TestAnnotation1 = {"A","B"}',
            'SET TestAnnotation2 = "X"',
            'g(TESTNS:1) -> g(TESTNS:2)'
        ]

        self.parser.parse_lines(statements)

        self.assertEqual(2, len(self.parser.control_parser.annotations))
        self.assertIn('TestAnnotation1', self.parser.control_parser.annotations)
        self.assertIn('TestAnnotation2', self.parser.control_parser.annotations)
        self.assertEqual(2, len(self.parser.control_parser.annotations['TestAnnotation1']))
        self.assertEqual(
            [
                Entity(namespace='TestAnnotation1', identifier='A'),
                Entity(namespace='TestAnnotation1', identifier='B'),
            ],
            self.parser.control_parser.annotations['TestAnnotation1'],
        )
        self.assertEqual(1, len(self.parser.control_parser.annotations['TestAnnotation2']))
        self.assertEqual(
            [
                Entity(namespace='TestAnnotation2', identifier='X'),
            ],
            self.parser.control_parser.annotations['TestAnnotation2'],
        )

        test_node_1_dict = Gene(namespace='TESTNS', name='1')
        test_node_2_dict = Gene(namespace='TESTNS', name='2')

        self.assertEqual(2, self.parser.graph.number_of_nodes())
        self.assertIn(test_node_1_dict, self.graph)
        self.assertIn(test_node_2_dict, self.graph)

        self.assertEqual(1, self.parser.graph.number_of_edges())

        kwargs = {
            RELATION: INCREASES,
            EVIDENCE: test_evidence_text,
            ANNOTATIONS: {
                'TestAnnotation1': {'A': True, 'B': True},
                'TestAnnotation2': {'X': True},
            },
            CITATION: test_citation_dict,
        }
        self.assert_has_edge(test_node_1_dict, test_node_2_dict, only=True, **kwargs)

    def test_annotations_with_multilist(self):
        self.add_default_provenance()

        statements = [
            'SET TestAnnotation1 = {"A","B"}',
            'SET TestAnnotation2 = "X"',
            'SET TestAnnotation3 = {"D","E"}',
            'g(TESTNS:1) -> g(TESTNS:2)',
        ]
        self.parser.parse_lines(statements)

        self.assertEqual(3, len(self.parser.control_parser.annotations))
        self.assertIn('TestAnnotation1', self.parser.control_parser.annotations)
        self.assertIn('TestAnnotation2', self.parser.control_parser.annotations)
        self.assertIn('TestAnnotation3', self.parser.control_parser.annotations)

        test_node_1 = Gene(namespace='TESTNS', name='1')
        test_node_2 = Gene(namespace='TESTNS', name='2')

        self.assertEqual(2, self.parser.graph.number_of_nodes())
        self.assertIn(test_node_1, self.graph)
        self.assertIn(test_node_2, self.graph)

        self.assertEqual(1, self.parser.graph.number_of_edges())

        kwargs = {
            RELATION: INCREASES,
            EVIDENCE: test_evidence_text,
            ANNOTATIONS: {
                'TestAnnotation1': {'A': True, 'B': True},
                'TestAnnotation2': {'X': True},
                'TestAnnotation3': {'D': True, 'E': True},
            },
            CITATION: test_citation_dict,
        }
        self.assert_has_edge(test_node_1, test_node_2, only=True, **kwargs)


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


class TestNomenclature(TemporaryCacheMixin):
    """Test that `BEP-0008 nomenclature <http://bep.bel.bio/published/BEP-0008.html>`_ gets validated properly."""

    def test_bep_0008(self):
        """Test parsing works right"""
        graph = from_bel_script(test_bel_with_obo, manager=self.manager)
        self.assertIn('hgnc', graph.namespace_pattern)
        self.assertEqual(r'\d+', graph.namespace_pattern['hgnc'])

        self.assertEqual(0, graph.number_of_warnings(), msg=',\n'.join(map(str, graph.warnings)))

        self.assertEqual(2, graph.number_of_nodes())
        self.assertIn(Protein(namespace='hgnc', identifier='391', name='AKT1'), graph)
        self.assertIn(Protein(namespace='hgnc', identifier='3236', name='EGFR'), graph)


if __name__ == '__main__':
    unittest.main()
