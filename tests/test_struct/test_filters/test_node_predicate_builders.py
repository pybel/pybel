# -*- coding: utf-8 -*-

"""Tests for functions for building node predicates."""

import unittest

from pybel import BELGraph
from pybel.constants import GENE, NAME, PROTEIN
from pybel.dsl import bioprocess, gene, protein
from pybel.struct import filter_nodes
from pybel.struct.filters import invert_node_predicate
from pybel.struct.filters.node_predicate_builders import (
    build_node_graph_data_search, build_node_key_search, build_node_name_search, data_missing_key_builder,
    function_inclusion_filter_builder,
)
from pybel.testing.utils import n


class TestFunctionInclusionFilterBuilder(unittest.TestCase):
    """Tests for the function_inclusion_filter_builder function."""

    def test_type_error(self):
        """Test that a type error is thrown for an invalid argument type."""
        with self.assertRaises(TypeError):
            function_inclusion_filter_builder(5)

    def test_empty_list_error(self):
        """Test that a value error is thrown for an empty list."""
        with self.assertRaises(ValueError):
            function_inclusion_filter_builder([])

    def test_single(self):
        """Test building a node predicate with a single function."""
        f = function_inclusion_filter_builder(GENE)

        p1 = protein(n(), n())
        g1 = gene(n(), n())

        g = BELGraph()
        g.add_node_from_data(p1)
        g.add_node_from_data(g1)

        self.assertIn(p1, g)
        self.assertIn(g1, g)

        self.assertFalse(f(g, p1))
        self.assertTrue(f(g, g1))

        f = invert_node_predicate(f)

        self.assertTrue(f(g, p1))
        self.assertFalse(f(g, g1))

    def test_multiple(self):
        """Test building a node predicate with multiple functions."""
        f = function_inclusion_filter_builder([GENE, PROTEIN])

        p1 = protein(n(), n())
        g1 = gene(n(), n())
        b1 = bioprocess(n(), n())

        g = BELGraph()
        g.add_node_from_data(p1)
        g.add_node_from_data(g1)
        g.add_node_from_data(b1)

        self.assertIn(p1, g)
        self.assertIn(g1, g)
        self.assertIn(b1, g)

        self.assertTrue(f(g, p1))
        self.assertTrue(f(g, g1))
        self.assertFalse(f(g, b1))

        f = invert_node_predicate(f)

        self.assertFalse(f(g, p1))
        self.assertFalse(f(g, g1))
        self.assertTrue(f(g, b1))


class TestNodePredicateBuilders(unittest.TestCase):
    """Tests for node predicate builders."""

    def test_data_missing_key_builder(self):
        """Test the data_missing_key_builder function."""
        graph = BELGraph()
        p1 = protein('HGNC', n())
        p2 = protein('HGNC', n())
        graph.add_node_from_data(p1)
        graph.add_node_from_data(p2)

        key, other_key = 'k1', 'k2'

        data_missing_key = data_missing_key_builder(key)

        graph.nodes[p1][key] = n()
        graph.nodes[p2][other_key] = n()

        nodes = set(filter_nodes(graph, data_missing_key))

        self.assertNotIn(p1, nodes)
        self.assertIn(p2, nodes)

    def test_build_node_data_search(self):
        """Test build_node_data_search."""

        def test_key_predicate(datum):
            """Check the data is greater than zero.

            :rtype: bool
            """
            return 0 < datum

        key = n()

        data_predicate = build_node_graph_data_search(key, test_key_predicate)

        graph = BELGraph()

        p1 = protein('HGNC', n())
        graph.add_node_from_data(p1)
        graph.nodes[p1][key] = 0
        self.assertFalse(data_predicate(graph, p1))

        p2 = protein('HGNC', n())
        graph.add_node_from_data(p2)
        graph.nodes[p2][key] = 5
        self.assertTrue(data_predicate(graph, p2))

        p3 = protein('HGNC', n())
        graph.add_node_from_data(p3)
        self.assertFalse(data_predicate(graph, p3))

    def test_build_node_key_search(self):
        """Test build_node_key_search."""
        node_key_search = build_node_key_search(query='app', key=NAME)
        node_name_search = build_node_name_search(query='app')

        graph = BELGraph()

        p1 = protein('HGNC', 'APP')
        graph.add_node_from_data(p1)
        self.assertTrue(node_key_search(graph, p1))
        self.assertTrue(node_name_search(graph, p1))

        p2 = protein('MGI', 'app')
        graph.add_node_from_data(p2)
        self.assertTrue(node_key_search(graph, p2))
        self.assertTrue(node_name_search(graph, p2))

        p3 = protein('HGNC', 'nope')
        graph.add_node_from_data(p3)
        self.assertFalse(node_key_search(graph, p3))
        self.assertFalse(node_name_search(graph, p3))
