# -*- coding: utf-8 -*-

import json
import unittest

from pybel import BELGraph
from pybel.constants import *
from pybel.struct.operations import (
    left_full_join, left_node_intersection_join, left_outer_join, node_intersection,
    union,
)

HGNC = 'HGNC'

p1 = PROTEIN, HGNC, 'a'
p2 = PROTEIN, HGNC, 'b'
p3 = PROTEIN, HGNC, 'c'


class TestLeftFullJoin(unittest.TestCase):
    """Tests the variants of the left full join, including the exhaustive vs. hash algorithms and calling by function
    or magic functions"""

    def setUp(self):
        g = BELGraph()

        g.add_simple_node(*p1)
        g.add_simple_node(*p2)

        g.add_edge(p1, p2, attr_dict={
            RELATION: INCREASES,
            CITATION: {
                CITATION_TYPE: 'PubMed',
                CITATION_REFERENCE: 1,
                CITATION_NAME: 'PMID1'
            },
            EVIDENCE: 'Evidence 1',
            ANNOTATIONS: {}
        })

        h = BELGraph()

        h.add_simple_node(*p1)
        h.add_simple_node(*p2)
        h.add_simple_node(*p3)

        h.node[p1]['EXTRANEOUS'] = 'MOST DEFINITELY'
        h.node[p3]['EXTRANEOUS'] = 'MOST DEFINITELY'

        h.add_edge(p1, p2, attr_dict={
            RELATION: INCREASES,
            CITATION: {
                CITATION_TYPE: 'PubMed',
                CITATION_REFERENCE: 1,
                CITATION_NAME: 'PMID1'
            },
            EVIDENCE: 'Evidence 1',
            ANNOTATIONS: {}
        })

        h.add_edge(p1, p2, attr_dict={
            RELATION: INCREASES,
            CITATION: {
                CITATION_TYPE: 'PubMed',
                CITATION_REFERENCE: 2,
                CITATION_NAME: 'PMID2'
            },
            EVIDENCE: 'Evidence 2',
            ANNOTATIONS: {}
        })

        h.add_edge(p1, p3, attr_dict={
            RELATION: INCREASES,
            CITATION: {
                CITATION_TYPE: 'PubMed',
                CITATION_REFERENCE: 1,
                CITATION_NAME: 'PMID1'
            },
            EVIDENCE: 'Evidence 3',
            ANNOTATIONS: {}
        })

        self.g = g
        self.h = h

    def help_check_initial_g(self, g):
        self.assertEqual(2, g.number_of_nodes())
        self.assertEqual(1, g.number_of_edges())

    def help_check_initial_h(self, h):
        self.assertEqual(3, self.h.number_of_nodes())
        self.assertEqual(3, self.h.number_of_edges())

    def test_initial(self):
        self.help_check_initial_g(self.g)
        self.help_check_initial_h(self.h)

    def help_check(self, j):
        self.assertNotIn('EXTRANEOUS', j.node[p1])
        self.assertIn('EXTRANEOUS', j.node[p3])
        self.assertEqual('MOST DEFINITELY', j.node[p3]['EXTRANEOUS'])

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
        self.help_check(self.g)
        self.help_check_initial_h(self.h)

    def test_full_hash_join(self):
        left_full_join(self.g, self.h, use_hash=True)
        self.help_check(self.g)
        self.help_check_initial_h(self.h)

    def test_full_exhaustive_join(self):
        left_full_join(self.g, self.h, use_hash=False)
        self.help_check(self.g)
        self.help_check_initial_h(self.h)

    def test_union_hash(self):
        j = union([self.g, self.h], use_hash=True)
        self.help_check(j)
        self.help_check_initial_g(self.g)
        self.help_check_initial_h(self.h)

    def test_union_exhaustive(self):
        j = union([self.g, self.h], use_hash=True)
        self.help_check(j)
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

        g.add_node(1)
        g.add_node(2)
        g.add_edge(1, 2)

        self.assertEqual(2, g.number_of_nodes())
        self.assertEqual(1, g.number_of_edges())

        h = BELGraph()
        h.add_node(1)
        h.add_node(3)
        h.add_node(4)
        h.add_edge(1, 3)
        h.add_edge(1, 4)

        h.add_node(5)
        h.add_node(6)
        h.add_edge(5, 6)

        h.add_node(7)

        self.g = g
        self.h = h

    def help(self, g, h):
        self.assertEqual(4, g.number_of_nodes())
        self.assertEqual({1, 2, 3, 4}, set(g.nodes_iter()))
        self.assertEqual(3, g.number_of_edges())
        self.assertEqual({(1, 2), (1, 3), (1, 4)}, set(g.edges_iter()))

        self.assertEqual(6, h.number_of_nodes())
        self.assertEqual({1, 3, 4, 5, 6, 7}, set(h.nodes_iter()))
        self.assertEqual(3, h.number_of_edges())
        self.assertEqual({(1, 3), (1, 4), (5, 6)}, set(h.edges_iter()))

    def test_initial(self):
        self.assertEqual(6, self.h.number_of_nodes())
        self.assertEqual({1, 3, 4, 5, 6, 7}, set(self.h.nodes_iter()))
        self.assertEqual(3, self.h.number_of_edges())
        self.assertEqual({(1, 3), (1, 4), (5, 6)}, set(self.h.edges_iter()))

    def test_in_place_type_failure(self):
        with self.assertRaises(TypeError):
            self.g &= None

    def test_type_failure(self):
        with self.assertRaises(TypeError):
            self.g & None

    def test_magic(self):
        # left_outer_join(g, h)
        self.g &= self.h
        self.help(self.g, self.h)

    def test_left_outer_hash_join(self):
        self.g &= self.h
        left_outer_join(self.g, self.h, use_hash=True)
        self.help(self.g, self.h)

    def test_left_outer_exhaustive_join(self):
        self.g &= self.h
        left_outer_join(self.g, self.h, use_hash=False)
        self.help(self.g, self.h)


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
        self.assertEqual({1, 3, 4, 5, 6, 7}, set(graph.nodes_iter()))
        self.assertEqual(3, graph.number_of_edges())
        self.assertEqual({(1, 3), (1, 4), (5, 6)}, set(graph.edges_iter()))

    def test_initialize(self):
        self.help_check_initialize_g(self.g)
        self.help_check_initialize_h(self.h)

    def help_check_join(self, j):
        self.assertEqual(2, j.number_of_nodes())
        self.assertEqual({1, 3}, set(j.nodes_iter()))
        self.assertEqual(1, j.number_of_edges())
        self.assertEqual({(1, 3), }, set(j.edges_iter()))

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
