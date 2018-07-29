# -*- coding: utf-8 -*-

"""Tests for data structures in PyBEL."""

import unittest

from six import string_types

from pybel import BELGraph
from pybel.constants import (
    CITATION_REFERENCE, CITATION_TYPE, CITATION_TYPE_PUBMED, IDENTIFIER, PART_OF,
    unqualified_edge_code,
)
from pybel.dsl import hgvs, protein
from pybel.testing.utils import n

PART_OF_CODE = unqualified_edge_code[PART_OF]


class TestGraphProperties(unittest.TestCase):
    """Test setting and access to graph properties."""

    def setUp(self):
        """Make fake metadata for the graphs."""
        (
            self.name,
            self.version,
            self.description,
            self.authors,
            self.contact,
            self.licenses,
            self.copyrights,
            self.disclaimer
        ) = [n() for _ in range(8)]

    def help_test_metadata(self, graph):
        """Help test the right metadata got in the graph.

        :type graph: BELGraph
        """
        self.assertEqual(self.name, graph.name)
        self.assertEqual(self.version, graph.version)
        self.assertEqual(self.description, graph.description)
        self.assertEqual(self.authors, graph.authors)
        self.assertEqual(self.contact, graph.contact)
        self.assertEqual(self.licenses, graph.license)
        self.assertEqual(self.copyrights, graph.copyright)
        self.assertEqual(self.disclaimer, graph.disclaimer)

        self.assertEqual('{name} v{version}'.format(name=self.name, version=self.version), str(graph))

    def test_str_kwargs(self):
        """Test setting of metadata through keyword arguments."""
        graph = BELGraph(
            name=self.name,
            version=self.version,
            description=self.description,
            authors=self.authors,
            contact=self.contact,
            license=self.licenses,
            copyright=self.copyrights,
            disclaimer=self.disclaimer
        )
        self.help_test_metadata(graph)

    def test_name(self):
        """Test setting of metadata through attributes."""
        graph = BELGraph()

        graph.name = self.name
        graph.version = self.version
        graph.description = self.description
        graph.authors = self.authors
        graph.contact = self.contact
        graph.license = self.licenses
        graph.copyright = self.copyrights
        graph.disclaimer = self.disclaimer

        self.help_test_metadata(graph)


class TestStruct(unittest.TestCase):
    """Test the BEL graph data structure."""

    def test_add_simple(self):
        """Test that a simple node can be added, but not duplicated."""
        graph = BELGraph()

        namespace, name = n(), n()

        graph.add_node_from_data(protein(namespace=namespace, name=name))
        self.assertEqual(1, graph.number_of_nodes())

        graph.add_node_from_data(protein(namespace=namespace, name=name))
        self.assertEqual(1, graph.number_of_nodes())

    def test_citation_type_error(self):
        """Test error handling on adding qualified edges."""
        graph = BELGraph()

        with self.assertRaises(TypeError):
            graph.add_increases(
                protein(namespace='TEST', name='YFG1'),
                protein(namespace='TEST', name='YFG2'),
                evidence=n(),
                citation=5,
            )


class TestGetGraphProperties(unittest.TestCase):
    """The tests in this class check the getting and setting of node properties."""

    def setUp(self):
        """Set up the test case with a fresh BEL graph."""
        self.graph = BELGraph()

    def test_get_qualified_edge(self):
        """Test adding an edge to a graph."""
        test_source = protein(namespace='TEST', name='YFG')
        test_target = protein(namespace='TEST', name='YFG2')

        self.graph.add_node_from_data(test_source)
        self.graph.add_node_from_data(test_target)

        test_key = n()
        test_evidence = n()
        test_pmid = n()

        self.graph.add_increases(
            test_source,
            test_target,
            citation=test_pmid,
            evidence=test_evidence,
            annotations={
                'Species': '9606',
                'Confidence': 'Very High'
            },
            key=test_key,
        )

        citation = self.graph.get_edge_citation(test_source.as_tuple(), test_target.as_tuple(), test_key)

        self.assertIsNotNone(citation)
        self.assertIsInstance(citation, dict)
        self.assertIn(CITATION_TYPE, citation)
        self.assertEqual(CITATION_TYPE_PUBMED, citation[CITATION_TYPE])
        self.assertIn(CITATION_REFERENCE, citation)
        self.assertEqual(test_pmid, citation[CITATION_REFERENCE])

        evidence = self.graph.get_edge_evidence(test_source.as_tuple(), test_target.as_tuple(), test_key)

        self.assertIsNotNone(evidence)
        self.assertIsInstance(evidence, string_types)
        self.assertEqual(test_evidence, evidence)

        annotations = self.graph.get_edge_annotations(test_source.as_tuple(), test_target.as_tuple(), test_key)
        self.assertIsNotNone(annotations)
        self.assertIsInstance(annotations, dict)
        self.assertIn('Species', annotations)
        self.assertIn('9606', annotations['Species'])
        self.assertTrue(annotations['Species']['9606'])
        self.assertIn('Confidence', annotations)
        self.assertIn('Very High', annotations['Confidence'])
        self.assertTrue(annotations['Confidence']['Very High'])

    def test_get_unqualified_edge(self):
        """Test adding an unqualified edge."""
        test_source = protein(namespace='TEST', name='YFG')
        test_target = protein(namespace='TEST', name='YFG2')

        self.graph.add_part_of(test_source, test_target)

        citation = self.graph.get_edge_citation(test_source.as_tuple(), test_target.as_tuple(), PART_OF_CODE)
        self.assertIsNone(citation)

        evidence = self.graph.get_edge_evidence(test_source.as_tuple(), test_target.as_tuple(), PART_OF_CODE)
        self.assertIsNone(evidence)

        annotations = self.graph.get_edge_annotations(test_source.as_tuple(), test_target.as_tuple(), PART_OF_CODE)
        self.assertIsNone(annotations)

    def test_get_node_name(self):
        """Test looking up the node name from the graph."""
        test_identifier = n()
        node = protein(namespace='TEST', identifier=test_identifier)
        node_tuple = self.graph.add_node_from_data(node)
        self.assertIsNone(self.graph.get_node_name(node_tuple))
        self.assertIsNotNone(self.graph.get_node_identifier(node_tuple))

    def test_get_node_identifier(self):
        """Test looking up the node identifier from the graph."""
        test_name = n()
        node = protein(namespace='TEST', name=test_name)
        self.graph.add_node_from_data(node)
        self.assertIsNotNone(self.graph.get_node_name(node.as_tuple()))
        self.assertIsNone(self.graph.get_node_identifier(node.as_tuple()))

    def test_get_node_properties(self):
        """Test looking up node properties."""
        test_name = n()
        test_identifier = n()

        node = protein(namespace='TEST', name=test_name, identifier=test_identifier)
        self.graph.add_node_from_data(node)

        self.assertEqual(test_name, self.graph.get_node_name(node.as_tuple()))
        self.assertEqual(test_identifier, self.graph.get_node_identifier(node.as_tuple()))

        self.assertIsNone(self.graph.get_node_description(node.as_tuple()))

        test_description = n()
        self.graph.set_node_description(node.as_tuple(), test_description)
        self.assertEqual(test_description, self.graph.get_node_description(node.as_tuple()))

    def test_add_node_with_variant(self):
        """Test that the identifier is carried through to the child."""
        graph = BELGraph()
        namespace, name, identifier, variant_name = n(), n(), n(), n()
        node = protein(namespace=namespace, name=name, identifier=identifier, variants=hgvs(variant_name))
        parent = node.get_parent()

        graph.add_node_from_data(node)

        self.assertEqual(2, graph.number_of_nodes())

        self.assertIn(IDENTIFIER, graph.node[node.as_tuple()])
        self.assertIn(IDENTIFIER, graph.node[parent.as_tuple()])
