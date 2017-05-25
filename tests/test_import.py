# -*- coding: utf-8 -*-

import logging
import tempfile
import time
import unittest
from pathlib import Path

import networkx as nx

from pybel import BELGraph
from pybel import to_bel_lines, from_lines
from pybel import to_bytes, from_bytes, to_graphml, from_path, from_url
from pybel import to_cx, from_cx, to_cx_jsons, from_cx_jsons
from pybel import to_json, from_json, to_jsons, from_jsons
from pybel import to_ndex, from_ndex
from pybel.constants import *
from pybel.parser import BelParser
from pybel.parser.parse_exceptions import *
from pybel.utils import hash_tuple
from tests.constants import AKT1, EGFR, CASP8, FADD, citation_1
from tests.constants import BelReconstitutionMixin, TestGraphMixin, TemporaryCacheClsMixin, TestTokenParserBase
from tests.constants import assertHasEdge, test_bel_isolated, test_bel_misordered
from tests.constants import test_bel_simple, SET_CITATION_TEST, test_citation_dict, test_set_evidence, \
    test_bel_thorough, test_bel_slushy, test_evidence_text
from tests.mocks import mock_bel_resources

logging.getLogger('requests').setLevel(logging.WARNING)
log = logging.getLogger(__name__)

evidence = 'Evidence 1'
testan1 = '1'


def do_remapping(original, reconstituted):
    """Remaps nodes to use the reconstitution tests
    
    :param BELGraph original: The original bel graph 
    :param BELGraph reconstituted: The reconstituted BEL graph from CX input/output
    """
    node_mapping = dict(enumerate(sorted(original.nodes_iter(), key=hash_tuple)))
    try:
        nx.relabel.relabel_nodes(reconstituted, node_mapping, copy=False)
    except KeyError as e:
        missing_nodes = set(node_mapping) - set(reconstituted.nodes_iter())
        log.exception('missing %s', [node_mapping[n] for n in missing_nodes])
        raise e


class TestThoroughIo(TemporaryCacheClsMixin, BelReconstitutionMixin):
    @classmethod
    def setUpClass(cls):
        super(TestThoroughIo, cls).setUpClass()

        @mock_bel_resources
        def get_thorough_graph(mock):
            return from_path(test_bel_thorough, manager=cls.manager, allow_nested=True)

        cls.thorough_graph = get_thorough_graph()

    def test_path(self):
        self.bel_thorough_reconstituted(self.thorough_graph)

    def test_bytes(self):
        graph_bytes = to_bytes(self.thorough_graph)
        graph = from_bytes(graph_bytes)
        self.bel_thorough_reconstituted(graph)

    def test_json(self):
        graph_json_dict = to_json(self.thorough_graph)
        graph = from_json(graph_json_dict)
        self.bel_thorough_reconstituted(graph)

    def test_jsons(self):
        graph_json_str = to_jsons(self.thorough_graph)
        graph = from_jsons(graph_json_str)
        self.bel_thorough_reconstituted(graph)

    def test_graphml(self):
        handle, path = tempfile.mkstemp()

        with open(path, 'wb') as f:
            to_graphml(self.thorough_graph, f)

    def test_cx(self):
        graph_cx_json_dict = to_cx(self.thorough_graph)
        reconstituted = from_cx(graph_cx_json_dict)

        do_remapping(self.thorough_graph, reconstituted)

        self.bel_thorough_reconstituted(reconstituted, check_warnings=False)

    def test_cxs(self):
        graph_cx_str = to_cx_jsons(self.thorough_graph)
        reconstituted = from_cx_jsons(graph_cx_str)

        do_remapping(self.thorough_graph, reconstituted)

        self.bel_thorough_reconstituted(reconstituted, check_warnings=False)

    def test_ndex_interchange(self):
        """Tests that a document can be uploaded and downloaded. Sleeps in the middle so that NDEx can process"""
        network_id = to_ndex(self.thorough_graph)
        time.sleep(15)
        reconstituted = from_ndex(network_id)

        do_remapping(self.thorough_graph, reconstituted)

        self.bel_thorough_reconstituted(reconstituted, check_warnings=False)

    @unittest.skip('Not sure if identifier is stable')
    def test_from_ndex(self):
        """Tests the download of a CX document from NDEx"""
        reconstituted = from_ndex('014e5957-3d96-11e7-8f50-0ac135e8bacf')

        do_remapping(self.thorough_graph, reconstituted)

        self.bel_thorough_reconstituted(reconstituted)

    def test_upgrade(self):
        lines = to_bel_lines(self.thorough_graph)
        reconstituted = from_lines(lines, manager=self.manager)
        self.bel_thorough_reconstituted(reconstituted)


class TestSlushyIo(TemporaryCacheClsMixin, BelReconstitutionMixin):
    @classmethod
    def setUpClass(cls):
        super(TestSlushyIo, cls).setUpClass()

        @mock_bel_resources
        def get_slushy_graph(mock):
            return from_path(test_bel_slushy, manager=cls.manager)

        cls.slushy_graph = get_slushy_graph()

    def test_slushy(self):
        self.bel_slushy_reconstituted(self.slushy_graph)

    def test_bytes(self):
        graph_bytes = to_bytes(self.slushy_graph)
        graph = from_bytes(graph_bytes)
        self.bel_slushy_reconstituted(graph)

    def test_json(self):
        graph_json = to_json(self.slushy_graph)
        graph = from_json(graph_json)
        self.bel_slushy_reconstituted(graph)

    def test_graphml(self):
        handle, path = tempfile.mkstemp()

        with open(path, 'wb') as f:
            to_graphml(self.slushy_graph, f)

    def test_bytes_io_slushy(self):
        g_bytes = to_bytes(self.slushy_graph)
        from_bytes(g_bytes)

    def test_cx(self):
        reconstituted = from_cx(to_cx(self.slushy_graph))

        do_remapping(self.slushy_graph, reconstituted)

        self.bel_slushy_reconstituted(reconstituted)

    def test_cxs(self):
        reconstituted = from_cx_jsons(to_cx_jsons(self.slushy_graph))

        do_remapping(self.slushy_graph, reconstituted)

        self.bel_slushy_reconstituted(reconstituted)


class TestSimpleIo(TemporaryCacheClsMixin, BelReconstitutionMixin):
    @classmethod
    def setUpClass(cls):
        super(TestSimpleIo, cls).setUpClass()

        @mock_bel_resources
        def get_simple_graph(mock_get):
            return from_url(Path(test_bel_simple).as_uri(), manager=cls.manager)

        cls.simple_graph = get_simple_graph()

    def test_compile(self):
        self.bel_simple_reconstituted(self.simple_graph)

    def test_cx(self):
        """Tests the CX input/output on test_bel.bel"""
        graph_cx_json = to_cx(self.simple_graph)

        reconstituted = from_cx(graph_cx_json)
        do_remapping(self.simple_graph, reconstituted)

        self.bel_simple_reconstituted(reconstituted)


class TestIsolatedIo(TemporaryCacheClsMixin, BelReconstitutionMixin, TestGraphMixin):
    @classmethod
    def setUpClass(cls):
        super(TestIsolatedIo, cls).setUpClass()

        @mock_bel_resources
        def get_isolated_graph(mock_get):
            return from_path(test_bel_isolated, manager=cls.manager)

        cls.isolated_graph = get_isolated_graph()

    def test_compile(self):
        self.bel_isolated_reconstituted(self.isolated_graph)

    def test_upgrade(self):
        lines = to_bel_lines(self.isolated_graph)
        reconstituted = from_lines(lines, manager=self.manager)
        self.bel_isolated_reconstituted(reconstituted)

    @mock_bel_resources
    def test_misordered(self, mock):
        """This test ensures that non-citation clearing mode works"""
        graph = from_path(test_bel_misordered, manager=self.manager, citation_clearing=False)
        self.assertEqual(4, graph.number_of_nodes())
        self.assertEqual(3, graph.number_of_edges())

        e1 = {
            RELATION: INCREASES,
            CITATION: citation_1,
            EVIDENCE: evidence,
            ANNOTATIONS: {
                'TESTAN1': testan1
            }
        }
        self.assertHasEdge(graph, AKT1, EGFR, **e1)

        e2 = {
            RELATION: DECREASES,
            CITATION: citation_1,
            EVIDENCE: evidence,
            ANNOTATIONS: {
                'TESTAN1': testan1
            }
        }
        self.assertHasEdge(graph, EGFR, FADD, **e2)

        e3 = {
            RELATION: DIRECTLY_DECREASES,
            CITATION: citation_1,
            EVIDENCE: evidence,
            ANNOTATIONS: {
                'TESTAN1': testan1
            }
        }
        self.assertHasEdge(graph, EGFR, CASP8, **e3)


class TestRegex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = BELGraph()
        cls.parser = BelParser(cls.graph, namespace_dict={}, namespace_regex={'dbSNP': 'rs[0-9]*'})

    def setUp(self):
        self.parser.clear()

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


class TestStuff(unittest.TestCase):
    def test_lenient_semantic_no_failure(self):
        statements = [
            SET_CITATION_TEST,
            test_set_evidence,
            "bp(ABASD) -- p(ABASF)"
        ]
        self.graph = BELGraph()
        self.parser = BelParser(self.graph, allow_naked_names=True)
        self.parser.parse_lines(statements)

        node_1 = BIOPROCESS, DIRTY, 'ABASD'
        node_2 = PROTEIN, DIRTY, 'ABASF'

        self.assertEqual({node_1, node_2}, set(self.graph.nodes_iter()))

        assertHasEdge(self, node_1, node_2, self.graph)


class TestFull(TestTokenParserBase):
    @classmethod
    def setUpClass(cls):
        cls.graph = BELGraph()
        cls.parser = BelParser(cls.graph, namespace_dict=namespaces, annotation_dict=annotations)

    def setUp(self):
        self.parser.clear()

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


if __name__ == '__main__':
    unittest.main()
