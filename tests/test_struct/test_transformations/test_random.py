# -*- coding: utf-8 -*-

"""Test for functions for inducing random sub-graphs."""

import random
import unittest

from pybel.struct.mutation.induction.random import get_graph_with_random_edges
from pybel.testing.generate import generate_random_graph


class TestRandom(unittest.TestCase):
    """Test random graph induction functions."""

    def test_random_edges(self):
        """Test getting a graph by random edges."""
        random.seed(127)  # love that number

        n_nodes, n_edges, n_sample_edges = 15, 80, 40
        graph = generate_random_graph(n_nodes=n_nodes, n_edges=n_edges)

        subgraph = get_graph_with_random_edges(graph, n_edges=n_sample_edges)
        self.assertEqual(n_sample_edges, subgraph.number_of_edges())
