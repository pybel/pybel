# -*- coding: utf-8 -*-

"""Tests for expansion functions."""

import unittest

from pybel import BELGraph
from pybel.examples.sialic_acid_example import (
    cd33, cd33_phosphorylated, shp1, shp2, sialic_acid, sialic_acid_cd33_complex, sialic_acid_graph, syk,
)
from pybel.struct.mutation.expansion.neighborhood import expand_node_neighborhood, expand_nodes_neighborhoods


class TestNeighborhood(unittest.TestCase):

    def test_neighborhood(self):
        graph = BELGraph()
        graph.add_node_from_data(cd33)
        self.assertEqual(1, graph.number_of_nodes())

        expand_node_neighborhood(sialic_acid_graph, graph, cd33.as_tuple())

        self.assertEqual(3, graph.number_of_nodes())
        self.assertIn(sialic_acid_cd33_complex.as_tuple(), graph)
        self.assertIn(cd33_phosphorylated.as_tuple(), graph)

    def test_neighborhood_with_predecessors(self):
        graph = BELGraph()
        graph.add_node_from_data(cd33)
        graph.add_node_from_data(sialic_acid_cd33_complex)
        self.assertEqual(3, graph.number_of_nodes())

        expand_node_neighborhood(sialic_acid_graph, graph, cd33.as_tuple())

        self.assertEqual(4, graph.number_of_nodes())
        self.assertIn(sialic_acid.as_tuple(), graph)
        self.assertIn(sialic_acid_cd33_complex.as_tuple(), graph)
        self.assertIn(cd33_phosphorylated.as_tuple(), graph)

    def test_neighborhood_with_successors(self):
        graph = BELGraph()
        graph.add_node_from_data(cd33)
        graph.add_node_from_data(cd33_phosphorylated)
        self.assertEqual(2, graph.number_of_nodes())

        expand_node_neighborhood(sialic_acid_graph, graph, cd33.as_tuple())

        self.assertEqual(3, graph.number_of_nodes())
        self.assertIn(sialic_acid_cd33_complex.as_tuple(), graph)
        self.assertIn(cd33_phosphorylated.as_tuple(), graph)

    def test_neighborhoods(self):
        """The edge between PTPN6/CD33ph should not be added"""
        graph = BELGraph()
        graph.add_node_from_data(cd33)
        graph.add_node_from_data(syk)
        self.assertEqual(2, graph.number_of_nodes())

        expand_nodes_neighborhoods(sialic_acid_graph, graph, [cd33.as_tuple(), syk.as_tuple()])

        self.assertNotIn(shp1.as_tuple(), graph[cd33_phosphorylated.as_tuple()])
        self.assertNotIn(shp2.as_tuple(), graph[cd33_phosphorylated.as_tuple()])

        self.assertEqual(8, graph.number_of_nodes(), msg='wrong number of nodes')
        self.assertEqual(8, graph.number_of_edges(), msg='wrong number of edges')
        self.assertIn(sialic_acid_cd33_complex.as_tuple(), graph)
        self.assertIn(cd33_phosphorylated.as_tuple(), graph)
