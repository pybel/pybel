# -*- coding: utf-8 -*-

"""Test for functions for inducing random sub-graphs."""

import random
import unittest
from collections import Counter

import networkx as nx

from pybel.struct.mutation.induction.random_subgraph import (
    get_graph_with_random_edges, get_random_node,
    get_random_subgraph,
)
from pybel.testing.generate import generate_random_graph


class TestRandom(unittest.TestCase):
    """Test random graph induction functions."""

    def setUp(self):
        """Set the random seed before each test."""
        random.seed(127)  # love that number

    def test_random_edges(self):
        """Test getting a graph by random edges."""
        n_nodes, n_edges, n_sample_edges = 15, 80, 40
        graph = generate_random_graph(n_nodes=n_nodes, n_edges=n_edges)

        subgraph = get_graph_with_random_edges(graph, n_edges=n_sample_edges)
        self.assertEqual(n_sample_edges, subgraph.number_of_edges())

    def test_random_nodes(self):
        """Test getting random nodes."""
        graph = nx.MultiDiGraph()

        graph.add_edge(1, 2)
        graph.add_edge(1, 3)
        graph.add_edge(1, 4)
        graph.add_edge(1, 5)

        n = 30000
        r = Counter(
            get_random_node(graph, set())
            for _ in range(n)
        )

        print(r)

        self.assertAlmostEqual(4 / 8, r[1] / n, places=2)
        self.assertAlmostEqual(1 / 8, r[2] / n, places=2)
        self.assertAlmostEqual(1 / 8, r[3] / n, places=2)
        self.assertAlmostEqual(1 / 8, r[4] / n, places=2)
        self.assertAlmostEqual(1 / 8, r[5] / n, places=2)

    def test_random_sample(self):
        n_nodes, n_edges = 50, 500
        graph = generate_random_graph(n_nodes=n_nodes, n_edges=n_edges)

        self.assertEqual(n_edges, graph.number_of_edges())

        sg = get_random_subgraph(graph, number_edges=250, number_seed_edges=5)
        self.assertEqual(250, sg.number_of_edges())

    def test_random_sample_small(self):
        n_nodes, n_edges = 11, 25
        graph = generate_random_graph(n_nodes, n_edges)

        self.assertEqual(n_edges, graph.number_of_edges())

        sg = get_random_subgraph(graph, number_edges=250, number_seed_edges=5)

        self.assertEqual(graph.number_of_edges(), sg.number_of_edges(),
                         msg='since graph is too small, the subgraph should contain the whole thing')
