# -*- coding: utf-8 -*-

"""Tests for edge predicates"""

import unittest

from pybel import BELGraph
from pybel.dsl import pathology, protein
from pybel.struct.filters.edge_predicates import has_pathology_causal
from pybel.testing.utils import n


class TestEdgePredicates(unittest.TestCase):
    """Tests for edge predicates."""

    def test_has_pathology(self):
        """Test for checking edges that have a causal pathology."""
        graph = BELGraph()

        a, b, c = protein(n(), n()), pathology(n(), n()), pathology(n(), n())

        key = graph.add_increases(a, b, citation=n(), evidence=n())
        self.assertFalse(has_pathology_causal(graph, a, b, key))

        key = graph.add_increases(b, a, citation=n(), evidence=n())
        self.assertTrue(has_pathology_causal(graph, b, a, key))

        key = graph.add_association(b, a, citation=n(), evidence=n())
        self.assertFalse(has_pathology_causal(graph, b, a, key))

        key = graph.add_increases(a, c, citation=n(), evidence=n())
        self.assertFalse(has_pathology_causal(graph, a, c, key))
