# -*- coding: utf-8 -*-

"""Tests for collapse functions."""

import unittest

from pybel import BELGraph
from pybel.constants import DIRECTLY_INCREASES
from pybel.dsl import gene, mirna, pathology, pmod, protein, rna
from pybel.struct.mutation.collapse import collapse_all_variants, collapse_nodes, collapse_to_genes
from pybel.testing.utils import n

HGNC = 'HGNC'
GO = 'GO'
CHEBI = 'CHEBI'

g1 = gene(HGNC, '1')
r1 = rna(HGNC, '1')
p1 = protein(HGNC, '1')
p1_phosphorylated = protein(HGNC, '1', variants=[pmod('Ph')])

g2 = gene(HGNC, '2')
r2 = rna(HGNC, '2')
p2 = protein(HGNC, '2')

g3 = gene(HGNC, '3')
r3 = rna(HGNC, '3')
p3 = protein(HGNC, '3')

g4 = gene(HGNC, '4')
m4 = mirna(HGNC, '4')

p5 = pathology(GO, '5')


class TestCollapse(unittest.TestCase):
    """Tests for collapse functions."""

    def test_collapse_by_dict(self):
        """Test collapsing nodes by a dictionary."""
        graph = BELGraph()
        graph.add_node_from_data(p1)
        graph.add_node_from_data(p2)
        graph.add_node_from_data(p3)

        graph.add_increases(p1, p3, citation=n(), evidence=n())
        graph.add_qualified_edge(p2, p3, relation=DIRECTLY_INCREASES, citation=n(), evidence=n())

        self.assertEqual(3, graph.number_of_nodes())
        self.assertEqual(2, graph.number_of_edges())

        d = {
            p1.as_tuple(): {p2.as_tuple()}
        }

        collapse_nodes(graph, d)

        self.assertEqual({p1.as_tuple(), p3.as_tuple()}, set(graph))
        self.assertEqual({(p1.as_tuple(), p3.as_tuple()), (p1.as_tuple(), p3.as_tuple())}, set(graph.edges()))
        self.assertEqual(1, graph.number_of_edges(), msg=graph.edges(data=True, keys=True))

    def test_collapse_dogma_1(self):
        """Test collapsing to genes, only with translations."""
        graph = BELGraph()
        graph.add_translation(r1, p1)

        self.assertEqual(2, graph.number_of_nodes())
        self.assertEqual(1, graph.number_of_edges())

        collapse_to_genes(graph)

        self.assertTrue(graph.has_node_with_data(g1))
        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())

    def test_collapse_dogma_2(self):
        """Test collapsing to genes with translations and transcriptions."""
        graph = BELGraph()
        graph.add_transcription(g1, r1)
        graph.add_translation(r1, p1)

        self.assertEqual(3, graph.number_of_nodes())
        self.assertEqual(2, graph.number_of_edges())

        collapse_to_genes(graph)

        self.assertTrue(graph.has_node_with_data(g1))
        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())

    def test_collapse_dogma_3(self):
        """Test collapsing to genes, only with transcriptions."""
        graph = BELGraph()
        graph.add_transcription(g1, r1)

        self.assertEqual(2, graph.number_of_nodes())
        self.assertEqual(1, graph.number_of_edges())

        collapse_to_genes(graph)

        self.assertTrue(graph.has_node_with_data(g1))
        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())

    def test_collapse_all_variants(self):
        """Test collapsing all variants to their reference nodes."""
        graph = BELGraph()
        graph.add_node_from_data(p1_phosphorylated)

        graph.add_increases(p1_phosphorylated, p2, n(), n())

        self.assertEqual(3, graph.number_of_nodes())
        self.assertEqual(2, graph.number_of_edges())

        collapse_all_variants(graph)

        self.assertEqual(2, graph.number_of_nodes())
        self.assertEqual(1, graph.number_of_edges())

        self.assertIn(p1.as_tuple(), graph)
        self.assertNotIn(p1_phosphorylated.as_tuple(), graph)
        self.assertIn(p2.as_tuple(), graph)
