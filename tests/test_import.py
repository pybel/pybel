import logging
import unittest

from pyparsing import ParseException

import pybel
from pybel.parser import BelParser
from pybel.parser.language import GENE
from pybel.parser.parse_exceptions import *
from tests import constants
from tests.constants import BelReconstitutionMixin, test_bel, TestTokenParserBase, test_citation_bel, \
    test_citation_dict, test_evidence_bel, mock_bel_resources, test_bel_thorough

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

    @mock_bel_resources
    def test_thorough(self, mock_get):
        g = pybel.from_path(test_bel_thorough)
        self.bel_thorough_reconstituted(g)

    @mock_bel_resources
    def test_slushy(self, mock_get):
        g = pybel.from_path(constants.test_bel_slushy)
        self.assertIsNotNone(g)

        self.assertEqual(25, g.warnings[0][0])
        self.assertIsInstance(g.warnings[0][2], NakedNameWarning)

        self.assertEqual(28, g.warnings[1][0])
        self.assertIsInstance(g.warnings[1][2], UndefinedNamespaceWarning)

        self.assertEqual(31, g.warnings[2][0])
        self.assertIsInstance(g.warnings[2][2], MissingNamespaceNameWarning)

        self.assertEqual(34, g.warnings[3][0])
        self.assertIsInstance(g.warnings[3][2], UndefinedAnnotationWarning)

        self.assertEqual(37, g.warnings[4][0])
        self.assertIsInstance(g.warnings[4][2], MissingAnnotationKeyWarning)

        self.assertEqual(40, g.warnings[5][0])
        self.assertIsInstance(g.warnings[5][2], IllegalAnnotationValueWarning)

        self.assertEqual(43, g.warnings[6][0])
        self.assertIsInstance(g.warnings[6][2], InvalidCitationException)

        self.assertEqual(47, g.warnings[7][0])
        self.assertIsInstance(g.warnings[7][2], MissingSupportWarning)

        self.assertEqual(51, g.warnings[8][0])
        self.assertIsInstance(g.warnings[8][2], MissingCitationException)

        self.assertEqual(54, g.warnings[9][0])
        self.assertIsInstance(g.warnings[9][2], InvalidPubMedIdentifierWarning)

        self.assertEqual(62, g.warnings[10][0])
        self.assertIsInstance(g.warnings[10][2], MalformedTranslocationWarning)

        self.assertEqual(65, g.warnings[11][0])
        self.assertIsInstance(g.warnings[11][2], PlaceholderAminoAcidWarning)

        self.assertEqual(68, g.warnings[12][0])
        self.assertIsInstance(g.warnings[12][2], NestedRelationWarning)

        self.assertEqual(71, g.warnings[13][0])
        self.assertIsInstance(g.warnings[13][2], InvalidFunctionSemantic)

        self.assertEqual(74, g.warnings[14][0])
        self.assertIsInstance(g.warnings[14][2], ParseException)

        self.assertEqual(77, g.warnings[15][0])
        self.assertIsInstance(g.warnings[15][2], ParseException)

        self.assertEqual(80, g.warnings[16][0])
        self.assertIsInstance(g.warnings[16][2], InvalidCitationType)


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

        test_node_1 = GENE, 'TESTNS', '1'
        test_node_2 = GENE, 'TESTNS', '2'

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

        test_node_1 = GENE, 'TESTNS', '1'
        test_node_2 = GENE, 'TESTNS', '2'

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

        test_node_1 = GENE, 'TESTNS', '1'
        test_node_2 = GENE, 'TESTNS', '2'

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
