import logging
import unittest

import pybel
from pybel.manager.cache import CacheManager
from pybel.parser import BelParser
from pybel.parser.parse_exceptions import InvalidFunctionSemantic, MissingCitationException
from tests.constants import BelReconstitutionMixin, test_bel, TestTokenParserBase, test_citation_bel, \
    test_citation_dict, test_evidence_bel, mock_bel_resources

logging.getLogger('requests').setLevel(logging.WARNING)


class TestImport(BelReconstitutionMixin, unittest.TestCase):

    @mock_bel_resources
    def test_bytes_io(self, mock_get):
        g = pybel.from_path(test_bel, complete_origin=True)
        self.bel_1_reconstituted(g)

        g_reloaded = pybel.from_bytes(pybel.to_bytes(g))
        self.bel_1_reconstituted(g_reloaded)

    @mock_bel_resources
    def test_from_fileUrl(self, mock_get):
        g = pybel.from_url('file://{}'.format(test_bel), complete_origin=True)
        self.bel_1_reconstituted(g)


class TestFull(TestTokenParserBase):
    def setUp(self):
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

        self.parser = BelParser(valid_namespaces=namespaces, valid_annotations=annotations)

    def test_semantic_failure(self):
        statement = "bp(TESTNS:1) -- p(TESTNS:2)"
        with self.assertRaises(InvalidFunctionSemantic):
            self.parser.parseString(statement)

    def test_missing_citation(self):
        statements = [
            test_evidence_bel,
            'SET TestAnnotation1 = "A"',
            'SET TestAnnotation2 = "X"',
            'g(TESTNS:1) -> g(TESTNS:2)'
        ]

        with self.assertRaises(MissingCitationException):
            self.parser.parse_lines(statements)

    def test_annotations(self):
        statements = [
            test_citation_bel,
            test_evidence_bel,
            'SET TestAnnotation1 = "A"',
            'SET TestAnnotation2 = "X"',
            'g(TESTNS:1) -> g(TESTNS:2)'
        ]
        self.parser.parse_lines(statements)

        test_node_1 = 'Gene', 'TESTNS', '1'
        test_node_2 = 'Gene', 'TESTNS', '2'

        self.assertEqual(2, self.parser.graph.number_of_nodes())
        self.assertHasNode(test_node_1)
        self.assertHasNode(test_node_2)

        self.assertEqual(1, self.parser.graph.number_of_edges())

        kwargs = {
            'TestAnnotation1': 'A',
            'TestAnnotation2': 'X',
            'citation': test_citation_dict
        }
        self.assertHasEdge(test_node_1, test_node_2, **kwargs)

    def test_annotations_withList(self):
        statements = [
            test_citation_bel,
            test_evidence_bel,
            'SET TestAnnotation1 = {"A","B"}',
            'SET TestAnnotation2 = "X"',
            'g(TESTNS:1) -> g(TESTNS:2)'
        ]
        self.parser.parse_lines(statements)

        test_node_1 = 'Gene', 'TESTNS', '1'
        test_node_2 = 'Gene', 'TESTNS', '2'

        self.assertEqual(2, self.parser.graph.number_of_nodes())
        self.assertHasNode(test_node_1)
        self.assertHasNode(test_node_2)

        self.assertEqual(2, self.parser.graph.number_of_edges())
        kwargs = {'TestAnnotation1': 'A', 'TestAnnotation2': 'X', 'citation': test_citation_dict}
        self.assertHasEdge(test_node_1, test_node_2, **kwargs)
        kwargs = {'TestAnnotation1': 'B', 'TestAnnotation2': 'X', 'citation': test_citation_dict}
        self.assertHasEdge(test_node_1, test_node_2, **kwargs)

    def test_annotations_withMultiList(self):
        statements = [
            test_citation_bel,
            test_evidence_bel,
            'SET TestAnnotation1 = {"A","B"}',
            'SET TestAnnotation2 = "X"',
            'SET TestAnnotation3 = {"D","E"}',
            'g(TESTNS:1) -> g(TESTNS:2)'
        ]
        self.parser.parse_lines(statements)

        test_node_1 = 'Gene', 'TESTNS', '1'
        test_node_2 = 'Gene', 'TESTNS', '2'

        self.assertEqual(2, self.parser.graph.number_of_nodes())
        self.assertHasNode(test_node_1)
        self.assertHasNode(test_node_2)

        self.assertEqual(4, self.parser.graph.number_of_edges())

        kwargs = {
            'TestAnnotation1': 'A',
            'TestAnnotation2': 'X',
            'TestAnnotation3': 'D',
            'citation': test_citation_dict
        }
        self.assertHasEdge(test_node_1, test_node_2, **kwargs)

        kwargs = {
            'TestAnnotation1': 'A',
            'TestAnnotation2': 'X',
            'TestAnnotation3': 'E',
            'citation': test_citation_dict
        }
        self.assertHasEdge(test_node_1, test_node_2, **kwargs)

        kwargs = {
            'TestAnnotation1': 'B',
            'TestAnnotation2': 'X',
            'TestAnnotation3': 'D',
            'citation': test_citation_dict
        }
        self.assertHasEdge(test_node_1, test_node_2, **kwargs)

        kwargs = {
            'TestAnnotation1': 'B',
            'TestAnnotation2': 'X',
            'TestAnnotation3': 'E',
            'citation': test_citation_dict
        }
        self.assertHasEdge(test_node_1, test_node_2, **kwargs)
