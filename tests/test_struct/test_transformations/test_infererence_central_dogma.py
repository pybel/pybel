# -*- coding: utf-8 -*-

"""Tests for inference of central dogma."""

import unittest

from pybel import BELGraph
from pybel.dsl import gene, hgvs, protein, protein_fusion, rna, rna_fusion
from pybel.struct.mutation import infer_central_dogma, prune_central_dogma
from pybel.testing.utils import n

trem2_gene = gene(namespace='HGNC', name='TREM2')
trem2_rna = rna(namespace='HGNC', name='TREM2')
trem2_protein = protein(namespace='HGNC', name='TREM2')


class TestProcessing(unittest.TestCase):
    """Test inference of the central dogma."""

    def assertInGraph(self, node, graph):
        """Assert the node is in the graph.

        :type node: pybel.dsl.BaseEntity
        :type graph: pybel.BELGraph
        :rtype: bool
        """
        self.assertTrue(graph.has_node_with_data(node))

    def assertNotInGraph(self, node, graph):
        """Assert the node is not in the graph.

        :type node: pybel.dsl.BaseEntity
        :type graph: pybel.BELGraph
        :rtype: bool
        """
        self.assertFalse(graph.has_node_with_data(node))

    def test_infer_on_sialic_acid_example(self):
        """Test infer_central_dogma on the sialic acid example."""
        graph = BELGraph()
        graph.add_node_from_data(trem2_protein)

        self.assertInGraph(trem2_protein, graph)
        self.assertNotInGraph(trem2_gene, graph)
        self.assertNotInGraph(trem2_rna, graph)

        infer_central_dogma(graph)

        self.assertInGraph(trem2_gene, graph)
        self.assertInGraph(trem2_rna, graph)

        prune_central_dogma(graph)

        self.assertNotInGraph(trem2_gene, graph)
        self.assertNotInGraph(trem2_rna, graph)

    def test_no_infer_on_protein_variants(self):
        p = protein('HGNC', n(), variants=[hgvs(n())])

        graph = BELGraph()
        graph.add_node_from_data(p)

        self.assertEqual(2, graph.number_of_nodes())
        self.assertEqual(1, graph.number_of_edges())

        infer_central_dogma(graph)

        self.assertEqual(4, graph.number_of_nodes())
        self.assertEqual(3, graph.number_of_edges())

    def test_no_infer_on_rna_variants(self):
        r = rna('HGNC', n(), variants=[hgvs(n())])

        graph = BELGraph()
        graph.add_node_from_data(r)

        self.assertEqual(2, graph.number_of_nodes())
        self.assertEqual(1, graph.number_of_edges())

        infer_central_dogma(graph)

        self.assertEqual(3, graph.number_of_nodes())
        self.assertEqual(2, graph.number_of_edges())

    def test_no_infer_protein_fusion(self):
        """Test that np gene is inferred from a RNA fusion node."""
        partner5p = protein(n(), n())
        partner3p = protein(n(), n())

        p = protein_fusion(partner_3p=partner3p, partner_5p=partner5p)

        graph = BELGraph()
        graph.add_node_from_data(p)

        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())

        infer_central_dogma(graph)

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

        infer_central_dogma(graph)

        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())
