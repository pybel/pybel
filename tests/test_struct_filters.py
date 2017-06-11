# -*- coding: utf-8 -*-

import unittest

from pybel import BELGraph
from pybel.struct.filters import (
    keep_node_permissive,
    filter_edges,
    keep_edge_permissive,
    get_nodes,
    count_passed_node_filter,
    count_passed_edge_filter,
)


def make_edge_iterator_set(it):
    return {(u, v) for u, v, _, _ in it}


class TestNodeFilters(unittest.TestCase):
    def setUp(self):
        self.universe = BELGraph()

        self.universe.add_edge(1, 2)
        self.universe.add_edge(2, 3)
        self.universe.add_edge(3, 7)
        self.universe.add_edge(1, 4)
        self.universe.add_edge(1, 5)
        self.universe.add_edge(5, 6)
        self.universe.add_edge(8, 2)

        self.graph = BELGraph()
        self.graph.add_edge(1, 2)

        self.all_universe_nodes = {1, 2, 3, 4, 5, 6, 7, 8}
        self.all_graph_nodes = {1, 2}

    def test_no_node_filter_argument(self):
        nodes = get_nodes(self.universe)
        self.assertEqual(self.all_universe_nodes, nodes)

    def test_keep_node_permissive(self):
        nodes = get_nodes(self.universe, keep_node_permissive)
        self.assertEqual(self.all_universe_nodes, nodes)

    def test_concatenate_single_node_filter(self):
        nodes = get_nodes(self.universe, [keep_node_permissive])
        self.assertEqual(self.all_universe_nodes, nodes)

    def test_concatenate_multiple_node_filters(self):
        def even(graph, node):
            return node % 2 == 0

        def big(graph, node):
            return node > 3

        nodes = get_nodes(self.universe, [even, big])
        self.assertEqual({4, 6, 8}, nodes)

        self.assertEqual(3, count_passed_node_filter(self.universe, [even, big]))

    def test_no_edge_filter(self):
        edges = make_edge_iterator_set(filter_edges(self.graph))
        self.assertEqual({(1, 2)}, edges)

    def test_keep_edge_permissive(self):
        edges = make_edge_iterator_set(filter_edges(self.graph, keep_edge_permissive))
        self.assertEqual({(1, 2)}, edges)

    def test_concatenate_single_edge_filter(self):
        edges = make_edge_iterator_set(filter_edges(self.graph, [keep_edge_permissive]))
        self.assertEqual({(1, 2)}, edges)

    def test_concatenate_multiple_edge_filter(self):
        def has_odd_source(graph, u, v, k, d):
            return u % 2 != 0

        def has_even_target(graph, u, v, k, d):
            return v % 2 == 0

        edges = make_edge_iterator_set(filter_edges(self.universe, [has_odd_source, has_even_target]))
        self.assertEqual({(1, 2), (1, 4), (5, 6)}, edges)

        self.assertEqual(3, count_passed_edge_filter(self.universe, [has_odd_source, has_even_target]))


if __name__ == '__main__':
    unittest.main()
