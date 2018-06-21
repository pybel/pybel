# -*- coding: utf-8 -*-

"""Tests for functions for building node predicates."""

import unittest

from pybel import BELGraph
from pybel.constants import GENE, PROTEIN
from pybel.dsl import bioprocess, gene, protein
from pybel.struct.filters import invert_node_predicate
from pybel.struct.filters.node_predicate_builders import function_inclusion_filter_builder
from pybel.testing.utils import n


class TestNodePredicateBuilders(unittest.TestCase):

    def test_type_error(self):
        with self.assertRaises(TypeError):
            function_inclusion_filter_builder(5)

    def test_empty_list_error(self):
        with self.assertRaises(ValueError):
            function_inclusion_filter_builder([])

    def test_single(self):
        f = function_inclusion_filter_builder(GENE)

        p1 = protein(n(), n())
        g1 = gene(n(), n())

        g = BELGraph()
        g.add_node_from_data(p1)
        g.add_node_from_data(g1)

        self.assertIn(p1.as_tuple(), g)
        self.assertIn(g1.as_tuple(), g)

        self.assertFalse(f(g, p1.as_tuple()))
        self.assertTrue(f(g, g1.as_tuple()))

        f = invert_node_predicate(f)

        self.assertTrue(f(g, p1.as_tuple()))
        self.assertFalse(f(g, g1.as_tuple()))

    def test_multiple(self):
        f = function_inclusion_filter_builder([GENE, PROTEIN])

        p1 = protein(n(), n())
        g1 = gene(n(), n())
        b1 = bioprocess(n(), n())

        g = BELGraph()
        g.add_node_from_data(p1)
        g.add_node_from_data(g1)
        g.add_node_from_data(b1)

        self.assertIn(p1.as_tuple(), g)
        self.assertIn(g1.as_tuple(), g)
        self.assertIn(b1.as_tuple(), g)

        self.assertTrue(f(g, p1.as_tuple()))
        self.assertTrue(f(g, g1.as_tuple()))
        self.assertFalse(f(g, b1.as_tuple()))

        f = invert_node_predicate(f)

        self.assertFalse(f(g, p1.as_tuple()))
        self.assertFalse(f(g, g1.as_tuple()))
        self.assertTrue(f(g, b1.as_tuple()))
