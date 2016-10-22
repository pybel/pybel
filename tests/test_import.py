import logging
import os
import unittest

import pybel
from pybel.manager import NamespaceCache
from pybel.parser import BelParser
from tests.constants import TestTokenParserBase, PYBEL_TEST_ALL

logging.getLogger('requests').setLevel(logging.WARNING)

dir_path = os.path.dirname(os.path.realpath(__file__))


@unittest.skipUnless(PYBEL_TEST_ALL, 'not enough memory on Travis-CI for this test')
class TestCacheIntegration(unittest.TestCase):
    def test_cached_winning(self):
        path = os.path.join(dir_path, 'bel', 'test_bel_3.bel')

        c_path = 'sqlite://'

        c = NamespaceCache(conn=c_path, setup_default_cache=False)

        with open(path) as f:
            g = pybel.BELGraph(f, ns_cache_path=c)

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


@unittest.skipUnless(PYBEL_TEST_ALL, 'not enough memory on Travis-CI for this test')
class TestImport(unittest.TestCase):
    def test_full(self):
        path = os.path.join(dir_path, 'bel', 'test_bel_1.bel')
        g = pybel.from_path(path)

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

    def test_from_url(self):
        g = pybel.from_url('http://resource.belframework.org/belframework/20150611/knowledge/full_abstract1.bel')
        self.assertIsNotNone(g)

    def test_from_fileUrl(self):
        path = os.path.join(dir_path, 'bel', 'test_bel_1.bel')
        g = pybel.from_url('file://{}'.format(path))
        self.assertIsNotNone(g)


@unittest.skipUnless(PYBEL_TEST_ALL, 'not enough memory on Travis-CI for this test')
class TestFull(TestTokenParserBase):
    def setUp(self):
        namespaces = {
            'TESTNS': {"1", "2"}
        }

        annotations = {
            'TestAnnotation1': {'A', 'B', 'C'},
            'TestAnnotation2': {'X', 'Y', 'Z'},
            'TestAnnotation3': {'D', 'E', 'F'}
        }

        self.parser = BelParser(valid_namespaces=namespaces, valid_annotations=annotations)

    def test_annotations(self):
        statements = [
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
        self.assertHasEdge(test_node_1, test_node_2, **{'TestAnnotation1': 'A', 'TestAnnotation2': 'X'})

    def test_annotations_withList(self):
        statements = [
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
        self.assertHasEdge(test_node_1, test_node_2, **{'TestAnnotation1': 'A', 'TestAnnotation2': 'X'})
        self.assertHasEdge(test_node_1, test_node_2, **{'TestAnnotation1': 'B', 'TestAnnotation2': 'X'})

    def test_annotations_withMultiList(self):
        statements = [
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
        self.assertHasEdge(test_node_1, test_node_2, **{
            'TestAnnotation1': 'A',
            'TestAnnotation2': 'X',
            'TestAnnotation3': 'D'
        })
        self.assertHasEdge(test_node_1, test_node_2, **{
            'TestAnnotation1': 'A',
            'TestAnnotation2': 'X',
            'TestAnnotation3': 'E'
        })
        self.assertHasEdge(test_node_1, test_node_2, **{
            'TestAnnotation1': 'B',
            'TestAnnotation2': 'X',
            'TestAnnotation3': 'D'
        })
        self.assertHasEdge(test_node_1, test_node_2, **{
            'TestAnnotation1': 'B',
            'TestAnnotation2': 'X',
            'TestAnnotation3': 'E'
        })
