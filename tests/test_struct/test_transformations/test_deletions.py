# -*- coding: utf-8 -*-

"""Tests for node deletion functions."""

import unittest

from pybel import BELGraph
from pybel.constants import POSITIVE_CORRELATION, RELATION
from pybel.dsl import CompositeAbundance, Protein, gene, hgvs, pathology, protein_fusion, rna, rna_fusion
from pybel.struct.mutation import (
    enrich_protein_and_rna_origins, prune_protein_rna_origins, remove_associations, remove_isolated_list_abundances,
    remove_pathologies,
)
from pybel.struct.mutation.utils import remove_isolated_nodes, remove_isolated_nodes_op
from pybel.testing.utils import n

trem2_gene = gene(namespace='HGNC', name='TREM2')
trem2_rna = rna(namespace='HGNC', name='TREM2')
trem2_protein = Protein(namespace='HGNC', name='TREM2')


class TestDeletions(unittest.TestCase):
    """Test cases for deletion functions."""

    def test_remove_pathologies(self):
        """Test removal of pathologies."""
        g = BELGraph()

        p1, p2, p3 = (Protein(namespace='HGNC', name=n()) for _ in range(3))
        d1, d2 = (pathology(namespace='MESH', name=n()) for _ in range(2))

        g.add_increases(p1, p2, citation=n(), evidence=n())
        g.add_increases(p2, p3, citation=n(), evidence=n())
        g.add_positive_correlation(p1, d1, citation=n(), evidence=n())
        g.add_positive_correlation(p2, d1, citation=n(), evidence=n())
        g.add_association(p2, d1, citation=n(), evidence=n())
        g.add_positive_correlation(d1, d2, citation=n(), evidence=n())
        g.add_positive_correlation(d1, d2, citation=n(), evidence=n())

        self.assertEqual(5, g.number_of_nodes())
        self.assertEqual(7, g.number_of_edges())
        self.assertEqual(2, len(g[p2][d1]))

        remove_associations(g)

        relations = list(g[p2][d1].values())
        self.assertEqual(1, len(relations))
        self.assertEqual(POSITIVE_CORRELATION, relations[0][RELATION])

        self.assertEqual(5, g.number_of_nodes())
        self.assertEqual(6, g.number_of_edges())
        self.assertEqual(5, g.number_of_nodes())

        remove_pathologies(g)

        self.assertTrue(p1, g)
        self.assertTrue(p2, g)
        self.assertTrue(p3, g)
        self.assertEqual(3, g.number_of_nodes())
        self.assertEqual(2, g.number_of_edges())

    def test_remove_isolated_in_place(self):
        """Test removing isolated nodes (in-place)."""
        g = BELGraph()

        g.add_edge(1, 2)
        g.add_edge(2, 3)
        g.add_node(4)

        remove_isolated_nodes(g)

        self.assertEqual(3, g.number_of_nodes())
        self.assertEqual(2, g.number_of_edges())

    def test_remove_isolated_out_of_place(self):
        """Test removing isolated nodes (out-of-place)."""
        g = BELGraph()

        g.add_edge(1, 2)
        g.add_edge(2, 3)
        g.add_node(4)

        g = remove_isolated_nodes_op(g)

        self.assertEqual(3, g.number_of_nodes())
        self.assertEqual(2, g.number_of_edges())

    def test_remove_isolated_list_abundances(self):
        """Test removing isolated list abundances."""
        g = BELGraph()
        p1, p2 = [Protein('HGNC', n()) for _ in range(2)]
        node = CompositeAbundance([p1, p2])
        g.add_node_from_data(node)
        self.assertEqual(3, g.number_of_nodes())
        remove_isolated_list_abundances(g)
        self.assertEqual(2, g.number_of_nodes())
        self.assertIn(p1, g)
        self.assertIn(p2, g)


class TestProcessing(unittest.TestCase):
    """Test inference of the central dogma."""

    def assert_in_graph(self, node, graph):
        """Assert the node is in the graph.

        :type node: pybel.dsl.BaseEntity
        :type graph: pybel.BELGraph
        :rtype: bool
        """
        self.assertIn(node, graph)

    def assert_not_in_graph(self, node, graph):
        """Assert the node is not in the graph.

        :type node: pybel.dsl.BaseEntity
        :type graph: pybel.BELGraph
        :rtype: bool
        """
        self.assertNotIn(node, graph)

    def test_infer_on_sialic_acid_example(self):
        """Test infer_central_dogma on the sialic acid example."""
        graph = BELGraph()
        graph.add_node_from_data(trem2_protein)

        self.assert_in_graph(trem2_protein, graph)
        self.assert_not_in_graph(trem2_gene, graph)
        self.assert_not_in_graph(trem2_rna, graph)

        enrich_protein_and_rna_origins(graph)

        self.assert_in_graph(trem2_gene, graph)
        self.assert_in_graph(trem2_rna, graph)

        prune_protein_rna_origins(graph)

        self.assert_not_in_graph(trem2_gene, graph)
        self.assert_not_in_graph(trem2_rna, graph)
        self.assert_in_graph(trem2_protein, graph)

    def test_no_infer_on_protein_variants(self):
        """Test that expansion doesn't occur on protein variants."""
        p = Protein('HGNC', n(), variants=[hgvs(n())])

        graph = BELGraph()
        graph.add_node_from_data(p)

        self.assertEqual(2, graph.number_of_nodes())
        self.assertEqual(1, graph.number_of_edges())

        enrich_protein_and_rna_origins(graph)

        self.assertEqual(4, graph.number_of_nodes())
        self.assertEqual(3, graph.number_of_edges())

    def test_no_infer_on_rna_variants(self):
        """Test that expansion doesn't occur on RNA variants."""
        r = rna('HGNC', n(), variants=[hgvs(n())])

        graph = BELGraph()
        graph.add_node_from_data(r)

        self.assertEqual(2, graph.number_of_nodes())
        self.assertEqual(1, graph.number_of_edges())

        enrich_protein_and_rna_origins(graph)

        self.assertEqual(3, graph.number_of_nodes())
        self.assertEqual(2, graph.number_of_edges())

    def test_no_infer_protein_fusion(self):
        """Test that no gene is inferred from a RNA fusion node."""
        partner5p = Protein(n(), n())
        partner3p = Protein(n(), n())

        p = protein_fusion(partner_3p=partner3p, partner_5p=partner5p)

        graph = BELGraph()
        graph.add_node_from_data(p)

        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())

        enrich_protein_and_rna_origins(graph)

        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())

    def test_no_infer_rna_fusion(self):
        """Test that no RNA nor gene is inferred from a protein fusion node."""
        partner5p = rna(n(), n())
        partner3p = rna(n(), n())

        p = rna_fusion(partner_3p=partner3p, partner_5p=partner5p)

        graph = BELGraph()
        graph.add_node_from_data(p)

        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())

        enrich_protein_and_rna_origins(graph)

        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())
