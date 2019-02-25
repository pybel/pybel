# -*- coding: utf-8 -*-

"""Test for functions for inducing random sub-graphs."""

import random
import sys
import unittest
from collections import Counter

import networkx as nx

from pybel.examples import sialic_acid_graph, statin_graph
from pybel.struct.mutation.induction.paths import get_random_path
from pybel.struct.mutation.induction.random_subgraph import (
    _helper, get_graph_with_random_edges, get_random_node, get_random_subgraph,
)
from pybel.testing.generate import generate_random_graph


@unittest.skipIf(sys.version_info < (3,), 'Will not support random operations on python2')
class TestRandom(unittest.TestCase):
    """Test random graph induction functions."""

    def setUp(self):
        """Set the random seed before each test."""
        random.seed(125)  # love that number

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
            get_random_node(graph, set(), invert_degrees=False)
            for _ in range(n)
        )

        degree_sum = 4 + 1 + 1 + 1 + 1

        self.assertAlmostEqual(4 / degree_sum, r[1] / n, places=2)
        self.assertAlmostEqual(1 / degree_sum, r[2] / n, places=2)
        self.assertAlmostEqual(1 / degree_sum, r[3] / n, places=2)
        self.assertAlmostEqual(1 / degree_sum, r[4] / n, places=2)
        self.assertAlmostEqual(1 / degree_sum, r[5] / n, places=2)

    def test_random_nodes_inverted(self):
        """Test getting random nodes."""
        graph = nx.MultiDiGraph()

        graph.add_edge(1, 2)
        graph.add_edge(1, 3)
        graph.add_edge(1, 4)
        graph.add_edge(1, 5)

        n = 30000
        r = Counter(
            get_random_node(graph, set(), invert_degrees=True)
            for _ in range(n)
        )

        degree_sum = (1 / 4) + (1 / 1) + (1 / 1) + (1 / 1) + (1 / 1)

        self.assertAlmostEqual((1 / 4) / degree_sum, r[1] / n, places=2)
        self.assertAlmostEqual((1 / 1) / degree_sum, r[2] / n, places=2)
        self.assertAlmostEqual((1 / 1) / degree_sum, r[3] / n, places=2)
        self.assertAlmostEqual((1 / 1) / degree_sum, r[4] / n, places=2)
        self.assertAlmostEqual((1 / 1) / degree_sum, r[5] / n, places=2)

    def test_random_sample(self):
        """Test randomly sampling a graph."""
        n_nodes, n_edges = 50, 500
        graph = generate_random_graph(n_nodes=n_nodes, n_edges=n_edges)

        self.assertEqual(n_edges, graph.number_of_edges())

        sg_1 = get_random_subgraph(graph, number_edges=250, number_seed_edges=10, invert_degrees=False)
        self.assertEqual(250, sg_1.number_of_edges())

        sg_2 = get_random_subgraph(graph, number_edges=250, number_seed_edges=10, invert_degrees=True)
        self.assertEqual(250, sg_2.number_of_edges())

    def test_random_sample_small(self):
        """Test a graph that is too small to sample."""
        n_nodes, n_edges = 11, 25
        graph = generate_random_graph(n_nodes, n_edges)

        self.assertEqual(n_edges, graph.number_of_edges())

        sg_1 = get_random_subgraph(graph, number_edges=250, number_seed_edges=5, invert_degrees=False)
        self.assertEqual(graph.number_of_edges(), sg_1.number_of_edges(),
                         msg='since graph is too small, the subgraph should contain the whole thing')

        sg_2 = get_random_subgraph(graph, number_edges=250, number_seed_edges=5, invert_degrees=True)
        self.assertEqual(graph.number_of_edges(), sg_2.number_of_edges(),
                         msg='since graph is too small, the subgraph should contain the whole thing')

    def test_helper_failure(self):
        graph = nx.MultiDiGraph()
        graph.add_edge(1, 2)
        graph.add_edge(2, 3)

        result = nx.MultiDiGraph()
        result.add_edge(1, 2)

        _helper(
            result,
            graph,
            number_edges_remaining=5,
            node_blacklist={1, 2, 3},
        )

        self.assertNotIn(3, result)


class TestRandomPath(unittest.TestCase):
    """Test getting random paths."""

    def test_get_random_path(self):
        """Test getting random paths doesn't crash."""
        for graph in (sialic_acid_graph, statin_graph):
            for _ in range(100):
                get_random_path(graph)
