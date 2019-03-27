# -*- coding: utf-8 -*-

"""Tests for graph operations."""

import unittest

from pybel import BELGraph
from pybel.dsl import protein
from pybel.struct.operations import (
    left_full_join, left_node_intersection_join, left_outer_join, node_intersection, union,
)
from pybel.testing.utils import n

p1, p2, p3, p4, p5, p6, p7, p8 = (protein(namespace='HGNC', name=n()) for _ in range(8))


class TestLeftFullJoin(unittest.TestCase):
    """Tests the variants of the left full join, including the exhaustive vs. hash algorithms and calling by function
    or magic functions"""

    def setUp(self):
        """Set up tests for the left full join with two example graphs."""
        g = BELGraph()
        g.add_increases(p1, p2, citation='PMID1', evidence='Evidence 1')

        self.tag = 'EXTRANEOUS'
        self.tag_value = 'MOST DEFINITELY'

        h = BELGraph()
        h.add_increases(p1, p2, citation='PMID1', evidence='Evidence 1')
        h.add_increases(p1, p2, citation='PMID2', evidence='Evidence 2')
        h.add_increases(p1, p3, citation='PMID1', evidence='Evidence 3')
        h.nodes[p1][self.tag] = self.tag_value
        h.nodes[p3][self.tag] = self.tag_value

        self.g = g
        self.h = h

        self.help_check_initial_g(self.g)
        self.help_check_initial_h(self.h)

    def help_check_initial_g(self, graph: BELGraph):
        """Test the initial G graph."""
        self.assertEqual(2, graph.number_of_nodes(), msg='initial graph G had wrong number of nodes')
        self.assertEqual(1, graph.number_of_edges(), msg='initial graph G had wrong number of edges')

    def help_check_initial_h(self, graph: BELGraph):
        """Test the initial H graph."""
        self.assertEqual(3, graph.number_of_nodes(), msg='initial graph H had wrong number of nodes')
        self.assertEqual(3, graph.number_of_edges(), msg='initial graph H had wrong number of edges')

    def help_check_result(self, j: BELGraph):
        """Help check the result of left joining H into G.

        :param j: The resulting graph from G += H
        """
        self.assertIn(self.tag, j.nodes[p1])
        self.assertNotIn(self.tag, j.nodes[p2])
        self.assertIn(self.tag, j.nodes[p3])
        self.assertEqual(self.tag_value, j.nodes[p1][self.tag])
        self.assertEqual(self.tag_value, j.nodes[p3][self.tag])

        self.assertEqual(3, j.number_of_nodes())
        self.assertEqual(3, j.number_of_edges(), msg="G edges:\n{}".format('\n'.join(map(str, j.edges(data=True)))))

    def test_function(self):
        """Test full joining two networks using the function."""
        left_full_join(self.g, self.h)
        self.help_check_result(self.g)
        self.help_check_initial_h(self.h)

    def test_full_join_with_isolated_nodes(self):
        """Test what happens when there are isolated nodes."""
        a = BELGraph()
        a.add_increases(p1, p2, citation=n(), evidence=n())
        a.add_node_from_data(p4)
        b = BELGraph()
        b.add_increases(p2, p3, citation=n(), evidence=n())
        b.add_node_from_data(p5)
        left_full_join(a, b)
        for node in p1, p2, p3, p4, p5:
            self.assertIn(node, a)

    def test_in_place_operator_failure(self):
        """Test that using the wrong type with the in-place addition operator raises an error."""
        with self.assertRaises(TypeError):
            self.g += None

    def test_in_place_operator(self):
        """Test full joining two networks using the BELGraph in-place addition operator."""
        self.g += self.h
        self.help_check_result(self.g)
        self.help_check_initial_h(self.h)

    def test_operator_failure(self):
        """Test that using the wrong type with the addition operator raises an error."""
        with self.assertRaises(TypeError):
            self.g + None

    def test_operator(self):
        """Test full joining two networks using the BELGraph addition operator."""
        j = self.g + self.h
        self.help_check_result(j)
        self.help_check_initial_g(self.g)
        self.help_check_initial_h(self.h)

    def test_union_failure(self):
        """Test that the union of no graphs raises a value error."""
        with self.assertRaises(ValueError):
            union([])

    def test_union_trivial(self):
        """Test that the union of a single graph returns that graph."""
        res = union([self.g])
        self.assertEqual(self.g, res)

    def test_union(self):
        """Test that the union of a pair of graphs is the same as the full join."""
        j = union([self.g, self.h])
        self.help_check_result(j)
        self.help_check_initial_g(self.g)
        self.help_check_initial_h(self.h)


class TestLeftFullOuterJoin(unittest.TestCase):
    def setUp(self):
        g = BELGraph()

        g.add_edge(p1, p2)

        h = BELGraph()
        h.add_edge(p1, p3)
        h.add_edge(p1, p4)

        h.add_edge(p5, p6)
        h.add_node(p7)

        self.g = g
        self.h = h

    def help_check_initial_g(self, g):
        self.assertEqual(2, g.number_of_nodes())
        self.assertEqual({p1, p2}, set(g))
        self.assertEqual(1, g.number_of_edges())
        self.assertEqual({(p1, p2)}, set(g.edges()))

    def help_check_initial_h(self, h):
        self.assertEqual(6, h.number_of_nodes())
        self.assertEqual({p1, p3, p4, p5, p6, p7}, set(h))
        self.assertEqual(3, h.number_of_edges())
        self.assertEqual({(p1, p3), (p1, p4), (p5, p6)}, set(h.edges()))

    def help_check_result(self, j):
        """After H has been full outer joined into G, this is what it should be"""
        self.assertEqual(4, j.number_of_nodes())
        self.assertEqual({p1, p2, p3, p4}, set(j))
        self.assertEqual(3, j.number_of_edges())
        self.assertEqual({(p1, p2), (p1, p3), (p1, p4)}, set(j.edges()))

    def test_in_place_type_failure(self):
        with self.assertRaises(TypeError):
            self.g &= None

    def test_type_failure(self):
        with self.assertRaises(TypeError):
            self.g & None

    def test_magic(self):
        # left_outer_join(g, h)
        self.g &= self.h
        self.help_check_initial_h(self.h)
        self.help_check_result(self.g)

    def test_operator(self):
        # left_outer_join(g, h)
        j = self.g & self.h
        self.help_check_initial_h(self.h)
        self.help_check_initial_g(self.g)
        self.help_check_result(j)

    def test_left_outer_join(self):
        left_outer_join(self.g, self.h)
        self.help_check_initial_h(self.h)
        self.help_check_result(self.g)

    def test_left_outer_exhaustive_join(self):
        self.g &= self.h
        left_outer_join(self.g, self.h)
        self.help_check_initial_h(self.h)
        self.help_check_result(self.g)


class TestInnerJoin(unittest.TestCase):
    """Tests various graph merging procedures"""

    def setUp(self):
        g = BELGraph()

        g.add_edge(p1, p2)
        g.add_edge(p1, p3)
        g.add_edge(p8, p3)

        h = BELGraph()
        h.add_edge(p1, p3)
        h.add_edge(p1, p4)
        h.add_edge(p5, p6)
        h.add_node(p7)

        self.g = g
        self.h = h

    def help_check_initialize_g(self, graph):
        self.assertEqual(4, graph.number_of_nodes())
        self.assertEqual(3, graph.number_of_edges())

    def help_check_initialize_h(self, graph):
        self.assertEqual(6, graph.number_of_nodes())
        self.assertEqual({p1, p3, p4, p5, p6, p7}, set(graph))
        self.assertEqual(3, graph.number_of_edges())
        self.assertEqual({(p1, p3), (p1, p4), (p5, p6)}, set(graph.edges()))

    def test_initialize(self):
        self.help_check_initialize_g(self.g)
        self.help_check_initialize_h(self.h)

    def help_check_join(self, j):
        self.assertEqual(2, j.number_of_nodes())
        self.assertEqual({p1, p3}, set(j))
        self.assertEqual(1, j.number_of_edges())
        self.assertEqual({(p1, p3), }, set(j.edges()))

    def test_in_place_type_failure(self):
        with self.assertRaises(TypeError):
            self.g ^ None

    def test_type_failure(self):
        with self.assertRaises(TypeError):
            self.g ^= None

    def test_magic(self):
        j = self.g ^ self.h
        self.help_check_join(j)
        self.help_check_initialize_h(self.h)
        self.help_check_initialize_g(self.g)

    def test_left_node_intersection_join(self):
        j = left_node_intersection_join(self.g, self.h)
        self.help_check_join(j)
        self.help_check_initialize_h(self.h)
        self.help_check_initialize_g(self.g)

    def test_node_intersection(self):
        j = node_intersection([self.h, self.g])
        self.help_check_join(j)
        self.help_check_initialize_h(self.h)
        self.help_check_initialize_g(self.g)

    def test_intersection_failure(self):
        with self.assertRaises(ValueError):
            node_intersection([])

    def test_intersection_trivial(self):
        res = node_intersection([self.g])
        self.assertEqual(self.g, res)


if __name__ == '__main__':
    unittest.main()
