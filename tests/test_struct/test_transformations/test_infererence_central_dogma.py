# -*- coding: utf-8 -*-

"""Tests for inference of central dogma."""

import unittest

from pybel import BELGraph
from pybel.dsl import gene, protein, rna
from pybel.struct.mutation import infer_central_dogma, prune_central_dogma

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
