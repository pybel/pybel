# -*- coding: utf-8 -*-

import unittest
from uuid import uuid4

from six import string_types

from pybel import BELGraph
from pybel.constants import (
    CITATION_REFERENCE, CITATION_TYPE, CITATION_TYPE_PUBMED, FUNCTION, GRAPH_METADATA,
    HAS_VARIANT, IDENTIFIER, INCREASES, METADATA_NAME, METADATA_VERSION, NAME, NAMESPACE, PROTEIN,
    unqualified_edge_code,
)
from pybel.dsl import *


class TestStruct(unittest.TestCase):
    def test_add_simple(self):
        g = BELGraph()

        g.add_node_from_data(protein(namespace='TEST', name='YFG'))
        self.assertEqual(1, g.number_of_nodes())

        g.add_node_from_data(protein(namespace='TEST', name='YFG'))
        self.assertEqual(1, g.number_of_nodes())

    def test_str(self):
        g = BELGraph(**{GRAPH_METADATA: {METADATA_NAME: 'test', METADATA_VERSION: '1.0.0'}})

        self.assertEqual('test', g.name)
        self.assertEqual('1.0.0', g.version)

        self.assertEqual('test v1.0.0', str(g))

    def test_str_kwargs(self):
        g = BELGraph(name='test', version='1.0.0', description='test description')

        self.assertEqual('test', g.name)
        self.assertEqual('1.0.0', g.version)
        self.assertEqual('test description', g.description)

        self.assertEqual('test v1.0.0', str(g))

    def test_name(self):
        g = BELGraph()

        g.name = 'test'
        g.version = '1.0.0'
        g.description = 'test description'

        self.assertEqual('test', g.name)
        self.assertEqual('1.0.0', g.version)
        self.assertEqual('test description', g.description)

        self.assertEqual('test v1.0.0', str(g))

    def test_citation_type_error(self):
        g = BELGraph()

        with self.assertRaises(TypeError):
            g.add_qualified_edge(
                protein(namespace='TEST', name='YFG1'),
                protein(namespace='TEST', name='YFG2'),
                relation=INCREASES,
                evidence=str(uuid4()),
                citation=5
            )


class TestDSL(unittest.TestCase):
    def test_add_robust_node(self):
        g = BELGraph()

        p = protein(name='yfg', namespace='test', identifier='1')

        p_tuple = g.add_node_from_data(p)

        self.assertEqual(
            {
                FUNCTION: PROTEIN,
                NAMESPACE: 'test',
                NAME: 'yfg',
                IDENTIFIER: '1'
            },
            g.node[p_tuple]
        )

    def test_add_identified_node(self):
        """What happens when a node with only an identifier is added to a graph"""
        g = BELGraph()

        p = protein(namespace='test', identifier='1')

        self.assertNotIn(NAME, p)

        p_tuple = g.add_node_from_data(p)

        self.assertEqual(
            {
                FUNCTION: PROTEIN,
                NAMESPACE: 'test',
                IDENTIFIER: '1'
            },
            g.node[p_tuple]
        )

    def test_missing_information(self):
        """Checks that entity and abundance functions raise on missing name/identifier"""
        with self.assertRaises(ValueError):
            entity(namespace='test')

        with self.assertRaises(ValueError):
            protein(namespace='test')


class TestGetGraphProperties(unittest.TestCase):
    """The tests in this class check the getting and setting of node properties"""

    def setUp(self):
        self.graph = BELGraph()

    def test_get_qualified_edge(self):
        test_source = self.graph.add_node_from_data(protein(namespace='TEST', name='YFG'))
        test_target = self.graph.add_node_from_data(protein(namespace='TEST', name='YFG2'))
        test_key = str(uuid4())
        test_evidence = str(uuid4())
        test_pmid = str(uuid4())

        self.graph.add_qualified_edge(
            test_source,
            test_target,
            relation=INCREASES,
            citation=test_pmid,
            evidence=test_evidence,
            annotations={
                'Species': '9606',
                'Confidence': 'Very High'
            },
            key=test_key
        )

        citation = self.graph.get_edge_citation(test_source, test_target, test_key)

        self.assertIsNotNone(citation)
        self.assertIsInstance(citation, dict)
        self.assertIn(CITATION_TYPE, citation)
        self.assertEqual(CITATION_TYPE_PUBMED, citation[CITATION_TYPE])
        self.assertIn(CITATION_REFERENCE, citation)
        self.assertEqual(test_pmid, citation[CITATION_REFERENCE])

        evidence = self.graph.get_edge_evidence(test_source, test_target, test_key)

        self.assertIsNotNone(evidence)
        self.assertIsInstance(evidence, string_types)
        self.assertEqual(test_evidence, evidence)

        annotations = self.graph.get_edge_annotations(test_source, test_target, test_key)
        self.assertIsNotNone(annotations)
        self.assertIsInstance(annotations, dict)
        self.assertIn('Species', annotations)
        self.assertIn('9606', annotations['Species'])
        self.assertTrue(annotations['Species']['9606'])
        self.assertIn('Confidence', annotations)
        self.assertIn('Very High', annotations['Confidence'])
        self.assertTrue(annotations['Confidence']['Very High'])

    def test_get_unqualified_edge(self):
        test_source = self.graph.add_node_from_data(protein(namespace='TEST', name='YFG'))
        test_target = self.graph.add_node_from_data(protein(namespace='TEST', name='YFG2'))

        self.graph.add_unqualified_edge(
            test_source,
            test_target,
            relation=HAS_VARIANT,
        )

        citation = self.graph.get_edge_citation(test_source, test_target, unqualified_edge_code[HAS_VARIANT])
        self.assertIsNone(citation)

        evidence = self.graph.get_edge_evidence(test_source, test_target, unqualified_edge_code[HAS_VARIANT])
        self.assertIsNone(evidence)

        annotations = self.graph.get_edge_annotations(test_source, test_target, unqualified_edge_code[HAS_VARIANT])
        self.assertIsNone(annotations)

    def test_get_node_name(self):
        test_identifier = str(uuid4())
        node = self.graph.add_node_from_data(protein(namespace='TEST', identifier=test_identifier))
        self.assertIsNone(self.graph.get_node_name(node))
        self.assertIsNotNone(self.graph.get_node_identifier(node))

    def test_get_node_identifier(self):
        test_name = str(uuid4())
        node = self.graph.add_node_from_data(protein(namespace='TEST', name=test_name))
        self.assertIsNotNone(self.graph.get_node_name(node))
        self.assertIsNone(self.graph.get_node_identifier(node))

    def test_get_node_properties(self):
        test_name = str(uuid4())
        test_identifier = str(uuid4())

        node = self.graph.add_node_from_data(protein(namespace='TEST', name=test_name, identifier=test_identifier))

        self.assertEqual(test_name, self.graph.get_node_name(node))
        self.assertEqual(test_identifier, self.graph.get_node_identifier(node))

        self.assertIsNone(self.graph.get_node_description(node))

        test_description = str(uuid4())
        self.graph.set_node_description(node, test_description)
        self.assertEqual(test_description, self.graph.get_node_description(node))


if __name__ == '__main__':
    unittest.main()
