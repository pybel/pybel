# -*- coding: utf-8 -*-

"""Tests for node deletion functions."""

import unittest

from pybel import BELGraph
from pybel.constants import ASSOCIATION, INCREASES, POSITIVE_CORRELATION, RELATION
from pybel.dsl import pathology, protein
from pybel.struct.mutation import remove_associations, remove_pathologies
from pybel.struct.mutation.utils import remove_isolated_nodes, remove_isolated_nodes_op
from pybel.testing.utils import n


class TestDeletions(unittest.TestCase):
    """Test cases for deletion functions."""

    def test_remove_pathologies(self):
        """Test removal of pathologies."""
        g = BELGraph()

        p1, p2, p3 = (protein(namespace='HGNC', name=n()) for _ in range(3))
        d1, d2 = (pathology(namespace='MESH', name=n()) for _ in range(2))

        g.add_qualified_edge(p1, p2, INCREASES, n(), n())
        g.add_qualified_edge(p2, p3, INCREASES, n(), n())
        g.add_qualified_edge(p1, d1, POSITIVE_CORRELATION, n(), n())
        g.add_qualified_edge(p2, d1, POSITIVE_CORRELATION, n(), n())
        g.add_qualified_edge(p2, d1, ASSOCIATION, n(), n())
        g.add_qualified_edge(d1, d2, POSITIVE_CORRELATION, n(), n())
        g.add_qualified_edge(d1, d2, POSITIVE_CORRELATION, n(), n())

        self.assertEqual(5, g.number_of_nodes())
        self.assertEqual(7, g.number_of_edges())
        self.assertEqual(2, len(g[p2.as_tuple()][d1.as_tuple()]))

        remove_associations(g)

        relations = list(g[p2.as_tuple()][d1.as_tuple()].values())
        self.assertEqual(1, len(relations))
        self.assertEqual(POSITIVE_CORRELATION, relations[0][RELATION])

        self.assertEqual(5, g.number_of_nodes())
        self.assertEqual(6, g.number_of_edges())
        self.assertEqual(5, g.number_of_nodes())

        remove_pathologies(g)

        self.assertTrue(g.has_node_with_data(p1))
        self.assertTrue(g.has_node_with_data(p2))
        self.assertTrue(g.has_node_with_data(p3))
        self.assertEqual(3, g.number_of_nodes())
        self.assertEqual(2, g.number_of_edges())

    def test_remove_isolated_in_place(self):
        g = BELGraph()

        g.add_edge(1, 2)
        g.add_edge(2, 3)
        g.add_node(4)

        remove_isolated_nodes(g)

        self.assertEqual(3, g.number_of_nodes())
        self.assertEqual(2, g.number_of_edges())

    def test_remove_isolated_out_of_place(self):
        g = BELGraph()

        g.add_edge(1, 2)
        g.add_edge(2, 3)
        g.add_node(4)

        g = remove_isolated_nodes_op(g)

        self.assertEqual(3, g.number_of_nodes())
        self.assertEqual(2, g.number_of_edges())
