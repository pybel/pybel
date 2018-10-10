# -*- coding: utf-8 -*-

"""Tests for node selection functions."""

import unittest

from pybel import BELGraph
from pybel.dsl import Protein
from pybel.struct.filters.node_selection import get_nodes_by_namespace


class TestNodeSelection(unittest.TestCase):
    """Tests for node selection functions."""

    def test_get_node_by_namespace(self):
        """Test getting nodes with a given namespace."""
        g = BELGraph()
        a = Protein(namespace='N1', name='a')
        b = Protein(namespace='N1', name='b')
        c = Protein(namespace='N2', name='c')
        d = Protein(namespace='N3', name='d')
        g.add_node_from_data(a)
        g.add_node_from_data(b)
        g.add_node_from_data(c)
        g.add_node_from_data(d)

        nodes = set(get_nodes_by_namespace(g, 'N1'))

        self.assertIn(a, nodes)
        self.assertIn(b, nodes)
        self.assertNotIn(c, nodes)
        self.assertNotIn(d, nodes)

        nodes = set(get_nodes_by_namespace(g, ('N1', 'N2')))

        self.assertIn(a, nodes)
        self.assertIn(b, nodes)
        self.assertIn(c, nodes)
        self.assertNotIn(d, nodes)
