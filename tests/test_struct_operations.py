# -*- coding: utf-8 -*-

import unittest

from pybel import BELGraph
from pybel.constants import *
from pybel.dsl import protein
from pybel.struct.graph import (
    left_full_join, left_node_intersection_join, left_outer_join, node_intersection,
    union,
)
from tests.utils import n

HGNC = 'HGNC'

p1 = protein(namespace=HGNC, name='a')
p2 = protein(namespace=HGNC, name='b')
p3 = protein(namespace=HGNC, name='c')

p1_tuple = p1.as_tuple()
p2_tuple = p2.as_tuple()
p3_tuple = p3.as_tuple()


class TestLeftFullJoin(unittest.TestCase):
    """Tests the variants of the left full join, including calling by function or magic operators"""

    def setUp(self):
        g = BELGraph()

        g.add_node_from_data(p1)
        g.add_node_from_data(p2)

        g.add_qualified_edge(p1, p2, relation=INCREASES, citation='PMID1', evidence='Evidence 1')

        h = BELGraph()

        h.add_node_from_data(p1)
        h.add_node_from_data(p2)
        h.add_node_from_data(p3)

        # this shouldn't get copied over since it's already in the graph
        h.nodes[p1_tuple]['EXTRANEOUS'] = 'MOST DEFINITELY'
        # this should get copied over since it's not already in the graph
        h.nodes[p3_tuple]['EXTRANEOUS'] = 'MOST DEFINITELY'

        h.add_qualified_edge(p1, p2, relation=INCREASES, citation='PMID1', evidence='Evidence 1')
        h.add_qualified_edge(p1, p2, relation=INCREASES, citation='PMID2', evidence='Evidence 2')
        h.add_qualified_edge(p1, p3, relation=INCREASES, citation='PMID1', evidence='Evidence 3')

        self.g = g
        self.h = h

    def help_check_initial_g(self, g):
        self.assertIsNotNone(g)
        self.assertIsInstance(g, BELGraph)

        self.assertEqual(2, g.number_of_nodes(), msg='initial graph G had wrong number of nodes')
        self.assertEqual(1, g.number_of_edges(), msg='initial graph G had wrong number of edges')

    def help_check_initial_h(self, h):
        self.assertIsNotNone(h)
        self.assertIsInstance(h, BELGraph)

        self.assertEqual(3, h.number_of_nodes(), msg='initial graph H had wrong number of nodes')
        self.assertEqual(3, h.number_of_edges(), msg='initial graph H had wrong number of edges')

    def test_initial(self):
        self.help_check_initial_g(self.g)
        self.help_check_initial_h(self.h)

    def help_check_result(self, j):
        """Helps check the result of left joining H into G

        :param pybel.BELGraph j: The resulting graph from G += H
        """
        self.assertIsNotNone(j)
        self.assertIsInstance(j, BELGraph)

        self.assertNotIn('EXTRANEOUS', j.nodes[p1_tuple])
        self.assertNotIn('EXTRANEOUS', j.nodes[p2_tuple])
        self.assertIn('EXTRANEOUS', j.nodes[p3_tuple])
        self.assertEqual('MOST DEFINITELY', j.nodes[p3_tuple]['EXTRANEOUS'])

        self.assertEqual(3, j.number_of_nodes())
        self.assertEqual(3, j.number_of_edges(), msg="G edges:\n{}".format(j.edges(data=True)))

    def test_full_join(self):
        left_full_join(self.g, self.h)
        self.help_check_result(self.g)
        self.help_check_initial_h(self.h)

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

    def test_operator(self):
        j = self.g + self.h
        self.help_check_result(j)
        self.help_check_initial_g(self.g)
        self.help_check_initial_h(self.h)

    def test_union(self):
        j = union([self.g, self.h])
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
    """This class tests :func:`pybel.struct.left_outer_join`"""

    def setUp(self):
        hgnc_dummy_url = n()

        self.n1 = protein(namespace='HGNC', name='1')
        self.n2 = protein(namespace='HGNC', name='2')
        self.n3 = protein(namespace='HGNC', name='3')
        self.n4 = protein(namespace='HGNC', name='4')
        self.n5 = protein(namespace='HGNC', name='5')
        self.n6 = protein(namespace='HGNC', name='6')
        self.n7 = protein(namespace='HGNC', name='7')

        g = BELGraph()
        g.namespace_url['HGNC'] = hgnc_dummy_url

        g.add_qualified_edge(self.n1, self.n2, relation=n(), citation=n(), evidence=n())

        h = BELGraph()
        h.namespace_url['HGNC'] = hgnc_dummy_url

        h.add_qualified_edge(self.n1, self.n3, relation=n(), citation=n(), evidence=n())
        h.add_qualified_edge(self.n1, self.n4, relation=n(), citation=n(), evidence=n())

        h.add_qualified_edge(self.n5, self.n6, relation=n(), citation=n(), evidence=n())
        h.add_node_from_data(self.n7)

        self.g = g
        self.h = h

    def test_left_outer_join(self):
        left_outer_join(self.g, self.h)
        self.help_check_initial_h(self.h)
        self.help_check_result(self.g)

    @unittest.skip  # FIXME this needs to work better
    def test_namespace_conflict(self):
        k = BELGraph()
        k.namespace_url['HGNC'] = n()

        with self.assertRaises(Exception):
            left_outer_join(self.g, k)

    def help_check_initial_g(self, g):
        self.assertIsNotNone(g)
        self.assertIsInstance(g, BELGraph)

        self.assertEqual(2, g.number_of_nodes())
        self.assertEqual({self.n1.as_tuple(), self.n2.as_tuple()}, set(g))

        self.assertEqual(1, g.number_of_edges())
        self.assertEqual({(self.n1.as_tuple(), self.n2.as_tuple())}, set(g.edges()))

    def help_check_initial_h(self, h):
        self.assertIsNotNone(h)
        self.assertIsInstance(h, BELGraph)

        self.assertEqual(6, h.number_of_nodes(), msg='initial h graph has wrong number of nodes')
        self.assertEqual(set(h), {
            x.as_tuple()
            for x in (self.n1, self.n3, self.n4, self.n5, self.n6, self.n7)
        }, msg='initial h graph has wrong nodes')

        self.assertEqual(3, h.number_of_edges(), msg='initial h graph has wrong number of edges')
        self.assertEqual(set(h.edges()), {
            (self.n1.as_tuple(), self.n3.as_tuple()),
            (self.n1.as_tuple(), self.n4.as_tuple()),
            (self.n5.as_tuple(), self.n6.as_tuple())
        }, msg='initial h graph has wrong edges')

    def help_check_result(self, j):
        """After H has been full outer joined into G, this is what it should be"""
        self.assertIsNotNone(j)
        self.assertIsInstance(j, BELGraph)

        self.assertEqual(4, j.number_of_nodes(), msg='result has wrong number of edges')
        self.assertEqual(set(j), {
            x.as_tuple()
            for x in (self.n1, self.n2, self.n3, self.n4)
        }, msg='result has wrong nodes')

        self.assertEqual(3, j.number_of_edges(), msg='result has wrong number of edges')
        self.assertEqual(set(j.edges()), {
            (self.n1.as_tuple(), self.n2.as_tuple()),
            (self.n1.as_tuple(), self.n3.as_tuple()),
            (self.n1.as_tuple(), self.n4.as_tuple())
        }, msg='result has wrong edges')

    def test_in_place_type_failure(self):
        with self.assertRaises(TypeError):
            self.g &= None

    def test_type_failure(self):
        with self.assertRaises(TypeError):
            self.g & None

    def test_in_place_operator_left_outer_join(self):
        # left_outer_join(g, h)
        self.g &= self.h
        self.help_check_initial_h(self.h)
        self.help_check_result(self.g)

    def test_operator_left_outer_join(self):
        # left_outer_join(g, h)
        j = self.g & self.h
        self.help_check_initial_h(self.h)
        self.help_check_initial_g(self.g)
        self.help_check_result(j)


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
        self.assertIsNotNone(graph)
        self.assertIsInstance(graph, BELGraph)
        self.assertEqual(4, graph.number_of_nodes())
        self.assertEqual(3, graph.number_of_edges())

    def help_check_initialize_h(self, graph):
        self.assertIsNotNone(graph)
        self.assertIsInstance(graph, BELGraph)
        self.assertEqual(6, graph.number_of_nodes())
        self.assertEqual({1, 3, 4, 5, 6, 7}, set(graph))
        self.assertEqual(3, graph.number_of_edges())
        self.assertEqual({(1, 3), (1, 4), (5, 6)}, set(graph.edges()))

    def test_initialize(self):
        self.help_check_initialize_g(self.g)
        self.help_check_initialize_h(self.h)

    def help_check_join(self, j):
        self.assertIsNotNone(j)
        self.assertIsInstance(j, BELGraph)
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
