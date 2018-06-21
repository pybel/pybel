# -*- coding: utf-8 -*-

"""Tests for expansion functions."""

import unittest

from pybel import BELGraph
from pybel.examples.sialic_acid_example import cd33, cd33_phosphorylated, sialic_acid_cd33_complex, sialic_acid_graph
from pybel.struct.mutation.expansion.neighborhood import expand_node_neighborhood


class TestNeighborhood(unittest.TestCase):

    def test_neighborhood(self):
        graph = BELGraph()
        graph.add_node_from_data(cd33)
        self.assertEqual(1, graph.number_of_nodes())

        expand_node_neighborhood(sialic_acid_graph, graph, cd33.as_tuple())

        self.assertEqual(3, graph.number_of_nodes())
        self.assertIn(sialic_acid_cd33_complex.as_tuple(), graph)
        self.assertIn(cd33_phosphorylated.as_tuple(), graph)
