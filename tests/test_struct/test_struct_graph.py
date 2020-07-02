# -*- coding: utf-8 -*-

"""Tests for data structures in PyBEL."""

import os
import random
import tempfile
import unittest
from io import StringIO

import pybel
import pybel.examples
from pybel import BELGraph
from pybel.constants import CITATION_DB, CITATION_IDENTIFIER, CITATION_TYPE_PUBMED
from pybel.dsl import hgvs, protein
from pybel.io.api import InvalidExtensionError
from pybel.testing.utils import n


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

    def _help_test_metadata(self, graph: BELGraph) -> None:
        """Help test the right metadata got in the graph."""
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
        self._help_test_metadata(graph)

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

        self._help_test_metadata(graph)


class TestStruct(unittest.TestCase):
    """Test the BEL graph data structure."""

    def test_add_simple(self):
        """Test that a simple node can be added, but not duplicated."""
        graph = BELGraph()
        node = protein(namespace='TEST', name='YFG')
        graph.add_node_from_data(node)
        self.assertEqual(1, graph.number_of_nodes())

        graph.add_node_from_data(node)
        self.assertEqual(1, graph.number_of_nodes(), msg='should not add same node again')

    def test_summarize(self):
        """Test summarizing a graph."""
        self.maxDiff = None
        sio = StringIO()

        random.seed(5)
        pybel.examples.sialic_acid_graph.version = '1.0.0'
        pybel.examples.sialic_acid_graph.summarize(file=sio, examples=False)
        test_str = """---------------------  -----------------
Name                   Sialic Acid Graph
Version                1.0.0
Number of Nodes        9
Number of Namespaces   3
Number of Edges        11
Number of Annotations  2
Number of Citations    1
Number of Authors      0
Network Density        1.53E-01
Number of Components   1
Number of Warnings     0
---------------------  -----------------

Type (3)      Count
----------  -------
Protein           7
Complex           1
Abundance         1

Namespace (2)      Count
---------------  -------
hgnc                   7
chebi                  1

Edge Type (7)                        Count
---------------------------------  -------
Protein increases Protein                3
Protein directlyIncreases Protein        2
Protein directlyDecreases Protein        2
Complex increases Protein                1
Abundance partOf Complex                 1
Protein partOf Complex                   1
Protein hasVariant Protein               1"""
        self.assertEqual(test_str.strip(), sio.getvalue().strip())

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

        test_evidence = n()
        test_pmid = n()

        test_key = self.graph.add_increases(
            test_source,
            test_target,
            citation=test_pmid,
            evidence=test_evidence,
            annotations={
                'Species': '9606',
                'Confidence': 'Very High'
            },
        )

        citation = self.graph.get_edge_citation(test_source, test_target, test_key)

        self.assertIsNotNone(citation)
        self.assertIsInstance(citation, dict)
        self.assertIn(CITATION_DB, citation)
        self.assertEqual(CITATION_TYPE_PUBMED, citation[CITATION_DB])
        self.assertIn(CITATION_IDENTIFIER, citation)
        self.assertEqual(test_pmid, citation[CITATION_IDENTIFIER])

        evidence = self.graph.get_edge_evidence(test_source, test_target, test_key)

        self.assertIsNotNone(evidence)
        self.assertIsInstance(evidence, str)
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
        """Test adding an unqualified edge."""
        test_source = protein(namespace='TEST', name='YFG')
        test_target = protein(namespace='TEST', name='YFG2')

        key = self.graph.add_part_of(test_source, test_target)

        citation = self.graph.get_edge_citation(test_source, test_target, key)
        self.assertIsNone(citation)

        evidence = self.graph.get_edge_evidence(test_source, test_target, key)
        self.assertIsNone(evidence)

        annotations = self.graph.get_edge_annotations(test_source, test_target, key)
        self.assertIsNone(annotations)

    def test_add_node_with_variant(self):
        """Test that the identifier is carried through to the child."""
        graph = BELGraph()
        namespace, name, identifier, variant_name = n(), n(), n(), n()
        node = protein(namespace=namespace, name=name, identifier=identifier, variants=hgvs(variant_name))
        node.get_parent()

        graph.add_node_from_data(node)

        self.assertEqual(2, graph.number_of_nodes())


class TestExtensionIO(unittest.TestCase):
    def test_io(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'ampk.bel.nodelink.json')
            pybel.dump(pybel.examples.ampk_graph, path)
            self.assertTrue(os.path.exists(path))
            new_graph = pybel.load(path)
            self.assertIsNotNone(new_graph)

    def test_invalid_io(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'ampk.bel.invalid.json')
            with self.assertRaises(InvalidExtensionError):
                pybel.dump(pybel.examples.ampk_graph, path)
            self.assertFalse(os.path.exists(path))
