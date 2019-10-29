# -*- coding: utf-8 -*-

"""Tests for expansion functions."""

import unittest

from pybel import BELGraph
from pybel.examples.sialic_acid_example import (
    cd33, cd33_phosphorylated, shp1, shp2, sialic_acid, sialic_acid_cd33_complex, sialic_acid_graph, syk,
)
from pybel.struct.mutation.expansion.neighborhood import (
    expand_node_neighborhood, expand_node_predecessors,
    expand_node_successors, expand_nodes_neighborhoods,
)


class TestExpansion(unittest.TestCase):
    """Test expansion functions."""

    def test_neighborhood(self):
        """Test expansion around the neighborhood of CD33 in the sialic acid graph given node."""
        graph = BELGraph()
        graph.add_node_from_data(cd33)
        self.assertEqual(1, graph.number_of_nodes())

        _sialic_acid_graph = sialic_acid_graph.copy()
        expand_node_neighborhood(graph=graph, universe=_sialic_acid_graph, node=cd33)

        self.assertEqual(
            {cd33, sialic_acid, sialic_acid_cd33_complex, cd33_phosphorylated},
            set(graph),
        )

    def test_neighborhood_with_predecessors(self):
        """Test expansion on the predecessors of a given node."""
        graph = BELGraph()
        graph.add_node_from_data(cd33)
        graph.add_node_from_data(sialic_acid_cd33_complex)
        self.assertEqual(3, graph.number_of_nodes())

        _sialic_acid_graph = sialic_acid_graph.copy()
        expand_node_predecessors(universe=_sialic_acid_graph, graph=graph, node=cd33)

        self.assertEqual(4, graph.number_of_nodes())
        self.assertIn(sialic_acid, graph)
        self.assertIn(sialic_acid_cd33_complex, graph)
        self.assertIn(cd33_phosphorylated, graph)

    def test_neighborhood_with_successors(self):
        """Test expansion on the successors of a given node."""
        graph = BELGraph()
        graph.add_node_from_data(cd33)
        graph.add_node_from_data(cd33_phosphorylated)
        self.assertEqual(2, graph.number_of_nodes())

        _sialic_acid_graph = sialic_acid_graph.copy()
        expand_node_successors(universe=_sialic_acid_graph, graph=graph, node=cd33)

        self.assertEqual(
            {sialic_acid_cd33_complex, sialic_acid, cd33_phosphorylated, cd33},
            set(graph),
        )

    def test_neighborhoods(self):
        """Test expansion on the neighborhood of given nodes.

        The edge between PTPN6/CD33ph should not be added.
        """
        graph = BELGraph()
        graph.add_node_from_data(cd33)
        graph.add_node_from_data(syk)
        self.assertEqual(2, graph.number_of_nodes())

        _sialic_acid_graph = sialic_acid_graph.copy()
        expand_nodes_neighborhoods(universe=_sialic_acid_graph, graph=graph, nodes=[cd33, syk])

        self.assertNotIn(shp1, graph[cd33_phosphorylated])
        self.assertNotIn(shp2, graph[cd33_phosphorylated])

        self.assertEqual(9, graph.number_of_nodes(), msg='wrong number of nodes: {}'.format(list(graph)))
        self.assertEqual(8, graph.number_of_edges(), msg='wrong number of edges')
        self.assertIn(sialic_acid, graph)
        self.assertIn(sialic_acid_cd33_complex, graph)
        self.assertIn(cd33_phosphorylated, graph)

    # TODO test that if new nodes with metadata that's missing (namespace_url definition, etc) then that gets added too
