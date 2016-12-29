import logging
import unittest

import pybel
from pybel.manager.cache import CacheManager
from pybel.parser import BelParser
from pybel.parser.parse_exceptions import IllegalFunctionSemantic, MissingCitationException
from tests.constants import TestTokenParserBase, test_bel_3, test_bel_1, test_citation_bel, test_citation_dict, \
    bel_1_reconstituted, test_evidence_bel

logging.getLogger('requests').setLevel(logging.WARNING)


class TestCacheIntegration(unittest.TestCase):
    def test_cached_winning(self):
        c_path = 'sqlite://'

        cm = CacheManager(connection=c_path)

        with open(test_bel_3) as f:
            g = pybel.BELGraph(f, cache_manager=cm)

        expected_document_metadata = {
            'Name': "PyBEL Test Document",
            "Description": "Made for testing PyBEL parsing",
            'Version': "1.6",
            'Copyright': "Copyright (c) Charles Tapley Hoyt. All Rights Reserved.",
            'Authors': "Charles Tapley Hoyt",
            'Licenses': "Other / Proprietary",
            'ContactInfo': "charles.hoyt@scai.fraunhofer.de"
        }

        self.assertEqual(expected_document_metadata, g.metadata_parser.document_metadata)


class TestImport(unittest.TestCase):
    def setUp(self):
        self.expected_document_metadata = {
            'Name': "PyBEL Test Document",
            "Description": "Made for testing PyBEL parsing",
            'Version': "1.6",
            'Copyright': "Copyright (c) Charles Tapley Hoyt. All Rights Reserved.",
            'Authors': "Charles Tapley Hoyt",
            'Licenses': "Other / Proprietary",
            'ContactInfo': "charles.hoyt@scai.fraunhofer.de"
        }

    def test_from_path(self):
        g = pybel.from_path(test_bel_1, complete_origin=True)
        self.assertEqual(self.expected_document_metadata, g.metadata_parser.document_metadata)
        bel_1_reconstituted(self, g)

    def test_from_fileUrl(self):
        g = pybel.from_url('file://{}'.format(test_bel_1), complete_origin=True)
        self.assertEqual(self.expected_document_metadata, g.metadata_parser.document_metadata)
        bel_1_reconstituted(self, g)


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
        with self.assertRaises(IllegalFunctionSemantic):
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
