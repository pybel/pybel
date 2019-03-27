# -*- coding: utf-8 -*-

import unittest
from typing import Set, Tuple

from pybel import BELGraph
from pybel.constants import ANNOTATIONS
from pybel.dsl import BaseEntity, Protein
from pybel.struct.filters import (
    and_edge_predicates, concatenate_node_predicates, count_passed_edge_filter, count_passed_node_filter, filter_edges,
    get_nodes, invert_edge_predicate,
)
from pybel.struct.filters.edge_predicate_builders import (
    _annotation_dict_all_filter, _annotation_dict_any_filter, build_annotation_dict_all_filter,
    build_annotation_dict_any_filter,
)
from pybel.struct.filters.edge_predicates import keep_edge_permissive
from pybel.struct.filters.node_predicates import keep_node_permissive
from pybel.struct.filters.typing import EdgeIterator
from pybel.testing.utils import n


def make_edge_iterator_set(it: EdgeIterator) -> Set[Tuple[BaseEntity, BaseEntity]]:
    return {(u, v) for u, v, _ in it}


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
        nodes = get_nodes(self.universe, [])
        self.assertEqual(self.all_universe_nodes, nodes)

    def test_keep_node_permissive(self):
        nodes = get_nodes(self.universe, keep_node_permissive)
        self.assertEqual(self.all_universe_nodes, nodes)

    def test_missing_node_filter(self):
        nodes = get_nodes(self.universe, concatenate_node_predicates([]))
        self.assertEqual(self.all_universe_nodes, nodes)

    def test_concatenate_single_node_filter(self):
        nodes = get_nodes(self.universe, [keep_node_permissive])
        self.assertEqual(self.all_universe_nodes, nodes)

    def test_concatenate_multiple_node_filters(self):
        def even(_, node) -> bool:
            return node % 2 == 0

        def big(_, node) -> bool:
            return node > 3

        nodes = get_nodes(self.universe, [even, big])
        self.assertEqual({4, 6, 8}, nodes)

        self.assertEqual(3, count_passed_node_filter(self.universe, [even, big]))

    def test_no_edge_filter(self):
        edges = make_edge_iterator_set(filter_edges(self.graph, []))
        self.assertEqual({(1, 2)}, edges)

    def test_keep_edge_permissive(self):
        edges = make_edge_iterator_set(filter_edges(self.graph, keep_edge_permissive))
        self.assertEqual({(1, 2)}, edges)

    def test_keep_edge_unpermissive(self):
        keep_edge_restrictive = invert_edge_predicate(keep_edge_permissive)
        edges = make_edge_iterator_set(filter_edges(self.graph, keep_edge_restrictive))
        self.assertEqual(set(), edges)

    def test_missing_edge_filter(self):
        edges = make_edge_iterator_set(filter_edges(self.graph, and_edge_predicates([])))
        self.assertEqual(({(1, 2)}), edges)

    def test_concatenate_single_edge_filter(self):
        edges = make_edge_iterator_set(filter_edges(self.graph, [keep_edge_permissive]))
        self.assertEqual({(1, 2)}, edges)

    def test_concatenate_multiple_edge_filter(self):
        def has_odd_source(graph, u, v, k):
            return u % 2 != 0

        def has_even_target(graph, u, v, k):
            return v % 2 == 0

        edges = make_edge_iterator_set(filter_edges(self.universe, [has_odd_source, has_even_target]))
        self.assertEqual({(1, 2), (1, 4), (5, 6)}, edges)

        self.assertEqual(3, count_passed_edge_filter(self.universe, [has_odd_source, has_even_target]))

        has_even_source = invert_edge_predicate(has_odd_source)
        edges = make_edge_iterator_set(filter_edges(self.universe, has_even_source))
        self.assertEqual({(2, 3), (8, 2)}, edges)


class TestEdgeFilters(unittest.TestCase):
    def test_a(self):
        self.assertTrue(_annotation_dict_any_filter(
            {ANNOTATIONS: {'A': {'1', '2'}}},
            {'A': {'1'}}
        ))

        self.assertTrue(_annotation_dict_any_filter(
            {ANNOTATIONS: {'A': {'1', '2'}}},
            {'A': {'1', '2'}}
        ))

        self.assertTrue(_annotation_dict_any_filter(
            {ANNOTATIONS: {'A': {'1', '2'}}},
            {'A': {'1', '2', '3'}}
        ))

        self.assertTrue(_annotation_dict_any_filter(
            {ANNOTATIONS: {'A': {'1', '2'}, 'B': {'X'}}},
            {'A': {'3'}, 'B': {'X'}}
        ))

        self.assertFalse(_annotation_dict_any_filter(
            {ANNOTATIONS: {'A': {'1', '2'}}},
            {'A': {'3'}}
        ))

        self.assertFalse(_annotation_dict_any_filter(
            {ANNOTATIONS: {'A': {'1', '2'}, 'B': {'X'}}},
            {'A': {'3'}, 'B': {'Y'}}
        ))

    def test_any_filter_no_query(self):
        """Test that the all filter returns true when there's no argument"""
        graph = BELGraph()
        graph.add_increases(Protein(n(), n()), Protein(n(), n()), citation=n(), evidence=n())
        self.assertEqual(1, count_passed_edge_filter(graph, build_annotation_dict_any_filter({})))

    def test_any_filter_no_annotations(self):
        graph = BELGraph()
        graph.add_increases(Protein(n(), n()), Protein(n(), n()), citation=n(), evidence=n())
        self.assertEqual(0, count_passed_edge_filter(graph, build_annotation_dict_any_filter({'A': {'1'}})))

    def test_any_filter_empty_annotations(self):
        graph = BELGraph()
        graph.add_increases(Protein(n(), n()), Protein(n(), n()), citation=n(), evidence=n(), annotations={})
        self.assertEqual(0, count_passed_edge_filter(graph, build_annotation_dict_any_filter({'A': {'1'}})))

    def test_any_filter(self):
        graph = BELGraph()
        graph.add_increases(Protein(n(), n()), Protein(n(), n()), citation=n(), evidence=n(), annotations={
            'A': {'1', '2', '3'}
        })

        self.assertEqual(1, count_passed_edge_filter(graph, build_annotation_dict_any_filter({'A': {'1'}})))
        self.assertEqual(1, count_passed_edge_filter(graph, build_annotation_dict_any_filter({'A': {'1', '2'}})))
        self.assertEqual(1, count_passed_edge_filter(graph, build_annotation_dict_any_filter({'A': {'1', '2', '3'}})))

    def test_b(self):
        self.assertTrue(_annotation_dict_all_filter(
            {ANNOTATIONS: {'A': {'1'}}},
            {'A': {'1'}}
        ))

        self.assertTrue(_annotation_dict_all_filter(
            {ANNOTATIONS: {'A': {'1', '2'}}},
            {'A': {'1', '2'}}
        ))

        self.assertTrue(_annotation_dict_all_filter(
            {ANNOTATIONS: {'A': {'1', '2'}}},
            {'A': {'1', '2'}}
        ))

        self.assertTrue(_annotation_dict_all_filter(
            {ANNOTATIONS: {'A': {'1', '2'}, 'B': {'X'}}},
            {'A': {'1', '2'}, 'B': {'X'}}
        ))

        self.assertFalse(_annotation_dict_all_filter(
            {ANNOTATIONS: {'A': {'1', '2'}, 'B': {'X'}}},
            {'A': {'1', '2', '3'}, 'B': {'X', 'Y'}}
        ))

        self.assertFalse(_annotation_dict_all_filter(
            {ANNOTATIONS: {'A': {'1'}}},
            {'A': {'1', '2'}}
        ))

        self.assertFalse(_annotation_dict_all_filter(
            {ANNOTATIONS: {'A': {'1'}}},
            {'A': {'2'}}
        ))

        self.assertFalse(_annotation_dict_all_filter(
            {ANNOTATIONS: {'A': {'1'}}},
            {'B': {'1'}}
        ))

    def test_all_filter_no_query(self):
        """Test that the all filter returns true when there's no argument"""
        graph = BELGraph()
        graph.add_increases(Protein(n(), n()), Protein(n(), n()), citation=n(), evidence=n())
        self.assertEqual(1, count_passed_edge_filter(graph, build_annotation_dict_all_filter({})))

    def test_all_filter_no_annotations(self):
        graph = BELGraph()
        graph.add_increases(Protein(n(), n()), Protein(n(), n()), citation=n(), evidence=n())
        self.assertEqual(0, count_passed_edge_filter(graph, build_annotation_dict_all_filter({'A': {'1'}})))

    def test_all_filter_empty_annotations(self):
        graph = BELGraph()
        graph.add_increases(Protein(n(), n()), Protein(n(), n()), citation=n(), evidence=n(), annotations={})
        self.assertEqual(0, count_passed_edge_filter(graph, build_annotation_dict_all_filter({'A': {'1'}})))

    def test_all_filter(self):
        graph = BELGraph()
        graph.add_increases(Protein(n(), n()), Protein(n(), n()), citation=n(), evidence=n(), annotations={
            'A': {'1', '2', '3'}
        })

        self.assertEqual(1, count_passed_edge_filter(graph, build_annotation_dict_all_filter({'A': {'1'}})))
        self.assertEqual(1, count_passed_edge_filter(graph, build_annotation_dict_all_filter({'A': {'1', '2'}})))
        self.assertEqual(1, count_passed_edge_filter(graph, build_annotation_dict_all_filter({'A': {'1', '2', '3'}})))
        self.assertEqual(0,
                         count_passed_edge_filter(graph, build_annotation_dict_all_filter({'A': {'1', '2', '3', '4'}})))
        self.assertEqual(0, count_passed_edge_filter(graph, build_annotation_dict_all_filter({'A': {'4'}})))

    def test_all_filter_dict(self):
        graph = BELGraph()
        graph.add_edge(1, 2, annotations={
            'A': {'1', '2', '3'}
        })

        self.assertEqual(1, count_passed_edge_filter(graph, build_annotation_dict_all_filter({'A': {'1': True}})))
        self.assertEqual(1, count_passed_edge_filter(graph, build_annotation_dict_all_filter({
            'A': {'1': True, '2': True}
        })))
        self.assertEqual(1, count_passed_edge_filter(graph, build_annotation_dict_all_filter({
            'A': {'1': True, '2': True, '3': True}
        })))
        self.assertEqual(0, count_passed_edge_filter(graph, build_annotation_dict_all_filter({
            'A': {'1': True, '2': True, '3': True, '4': True}
        })))
        self.assertEqual(0, count_passed_edge_filter(graph, build_annotation_dict_all_filter({
            'A': {'4': True}
        })))


if __name__ == '__main__':
    unittest.main()
