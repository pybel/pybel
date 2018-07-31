# -*- coding: utf-8 -*-

import json
import unittest

from pybel import BELGraph
from pybel.dsl import protein
from pybel.struct.operations import (
    left_full_join, left_node_intersection_join, left_outer_join, node_intersection, union,
)

HGNC = 'HGNC'

p1 = protein(namespace=HGNC, name='a')
p2 = protein(namespace=HGNC, name='b')
p3 = protein(namespace=HGNC, name='c')

p1_tuple = p1.as_tuple()
p2_tuple = p2.as_tuple()
p3_tuple = p3.as_tuple()


class TestLeftFullJoin(unittest.TestCase):
    """Tests the variants of the left full join, including the exhaustive vs. hash algorithms and calling by function
    or magic functions"""

    def setUp(self):
        g = BELGraph()

        g.add_node_from_data(p1)
        g.add_node_from_data(p2)

        g.add_increases(p1, p2, citation='PMID1', evidence='Evidence 1')

        h = BELGraph()

        h.add_node_from_data(p1)
        h.add_node_from_data(p2)
        h.add_node_from_data(p3)

        h.node[p1_tuple]['EXTRANEOUS'] = 'MOST DEFINITELY'
        h.node[p3_tuple]['EXTRANEOUS'] = 'MOST DEFINITELY'

        h.add_increases(p1, p2, citation='PMID1', evidence='Evidence 1')
        h.add_increases(p1, p2, citation='PMID2', evidence='Evidence 2')
        h.add_increases(p1, p3, citation='PMID1', evidence='Evidence 3')

        self.g = g
        self.h = h

    def help_check_initial_g(self, g):
        self.assertEqual(2, g.number_of_nodes(), msg='initial graph G had wrong number of nodes')
        self.assertEqual(1, g.number_of_edges(), msg='initial graph G had wrong number of edges')

    def help_check_initial_h(self, h):
        self.assertEqual(3, h.number_of_nodes(), msg='initial graph H had wrong number of nodes')
        self.assertEqual(3, h.number_of_edges(), msg='initial graph H had wrong number of edges')

    def test_initial(self):
        self.help_check_initial_g(self.g)
        self.help_check_initial_h(self.h)

    def help_check_result(self, j):
        """Helps check the result of left joining H into G

        :param pybel.BELGraph j: The resulting graph from G += H
        """
        self.assertIn('EXTRANEOUS', j.node[p1_tuple])
        self.assertNotIn('EXTRANEOUS', j.node[p2_tuple])
        self.assertIn('EXTRANEOUS', j.node[p3_tuple])

        self.assertEqual('MOST DEFINITELY', j.node[p1_tuple]['EXTRANEOUS'])
        self.assertEqual('MOST DEFINITELY', j.node[p3_tuple]['EXTRANEOUS'])

        self.assertEqual(3, j.number_of_nodes())
        self.assertEqual(3, j.number_of_edges(), msg="G edges:\n{}".format(json.dumps(j.edges(data=True), indent=2)))

    def test_in_place_type_failure(self):
        with self.assertRaises(TypeError):
            self.g += None

    def test_type_failure(self):
        with self.assertRaises(TypeError):
            self.g + None

    def test_magic(self):
        self.g += self.h
        self.help_check_result(self.g)
        self.help_check_initial_h(self.h)

    def test_full_hash_join(self):
        left_full_join(self.g, self.h, use_hash=True)
        self.help_check_result(self.g)
        self.help_check_initial_h(self.h)

    def test_full_exhaustive_join(self):
        left_full_join(self.g, self.h, use_hash=False)
        self.help_check_result(self.g)
        self.help_check_initial_h(self.h)

    def test_operator(self):
        j = self.g + self.h
        self.help_check_result(j)
        self.help_check_initial_g(self.g)
        self.help_check_initial_h(self.h)

    def test_union_hash(self):
        j = union([self.g, self.h], use_hash=True)
        self.help_check_result(j)
        self.help_check_initial_g(self.g)
        self.help_check_initial_h(self.h)

    def test_union_exhaustive(self):
        j = union([self.g, self.h], use_hash=True)
        self.help_check_result(j)
        self.help_check_initial_g(self.g)
        self.help_check_initial_h(self.h)

    def test_union_failure(self):
        with self.assertRaises(ValueError):
            union([])

    def test_union_trivial(self):
        res = union([self.g])
        self.assertEqual(self.g, res)


class TestLeftFullOuterJoin(unittest.TestCase):
    def setUp(self):
        g = BELGraph()

        g.add_edge(1, 2)

        h = BELGraph()
        h.add_edge(1, 3)
        h.add_edge(1, 4)

        h.add_edge(5, 6)
        h.add_node(7)

        self.g = g
        self.h = h

    def help_check_initial_g(self, g):
        self.assertEqual(2, g.number_of_nodes())
        self.assertEqual({1, 2}, set(g))
        self.assertEqual(1, g.number_of_edges())
        self.assertEqual({(1, 2)}, set(g.edges()))

    def help_check_initial_h(self, h):
        self.assertEqual(6, h.number_of_nodes())
        self.assertEqual({1, 3, 4, 5, 6, 7}, set(h))
        self.assertEqual(3, h.number_of_edges())
        self.assertEqual({(1, 3), (1, 4), (5, 6)}, set(h.edges()))

    def help_check_result(self, j):
        """After H has been full outer joined into G, this is what it should be"""
        self.assertEqual(4, j.number_of_nodes())
        self.assertEqual({1, 2, 3, 4}, set(j))
        self.assertEqual(3, j.number_of_edges())
        self.assertEqual({(1, 2), (1, 3), (1, 4)}, set(j.edges()))

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

    def test_left_outer_hash_join(self):
        left_outer_join(self.g, self.h, use_hash=True)
        self.help_check_initial_h(self.h)
        self.help_check_result(self.g)

    def test_left_outer_exhaustive_join(self):
        self.g &= self.h
        left_outer_join(self.g, self.h, use_hash=False)
        self.help_check_initial_h(self.h)
        self.help_check_result(self.g)


class TestInnerJoin(unittest.TestCase):
    """Tests various graph merging procedures"""

    def setUp(self):
        g = BELGraph()

        g.add_edge(1, 2)
        g.add_edge(1, 3)
        g.add_edge(8, 3)

        h = BELGraph()
        h.add_edge(1, 3)
        h.add_edge(1, 4)
        h.add_edge(5, 6)
        h.add_node(7)

        self.g = g
        self.h = h

    def help_check_initialize_g(self, graph):
        self.assertEqual(4, graph.number_of_nodes())
        self.assertEqual(3, graph.number_of_edges())

    def help_check_initialize_h(self, graph):
        self.assertEqual(6, graph.number_of_nodes())
        self.assertEqual({1, 3, 4, 5, 6, 7}, set(graph))
        self.assertEqual(3, graph.number_of_edges())
        self.assertEqual({(1, 3), (1, 4), (5, 6)}, set(graph.edges()))

    def test_initialize(self):
        self.help_check_initialize_g(self.g)
        self.help_check_initialize_h(self.h)

    def help_check_join(self, j):
        self.assertEqual(2, j.number_of_nodes())
        self.assertEqual({1, 3}, set(j))
        self.assertEqual(1, j.number_of_edges())
        self.assertEqual({(1, 3), }, set(j.edges()))

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

    def test_left_node_intersection_hash_join(self):
        j = left_node_intersection_join(self.g, self.h, use_hash=True)
        self.help_check_join(j)
        self.help_check_initialize_h(self.h)
        self.help_check_initialize_g(self.g)

    def test_left_node_intersection_exhaustive_join(self):
        j = left_node_intersection_join(self.g, self.h, use_hash=False)
        self.help_check_join(j)
        self.help_check_initialize_h(self.h)
        self.help_check_initialize_g(self.g)

    def test_node_intersection(self):
        j = node_intersection([self.h, self.g], use_hash=True)
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
