# -*- coding: utf-8 -*-

"""Tests for the mocks for the query builder."""

import unittest

from pybel.examples import egf_graph
from pybel.testing.mock_manager import MockQueryManager


class TestMockManager(unittest.TestCase):
    """Tests for the mock query manager."""

    def test_make(self):
        """Test instantiating the mock query manager."""
        manager = MockQueryManager()
        self.assertEqual(0, manager.count_networks())

    def test_make_with_graph(self):
        """Test counting networks in the mock query manager."""
        manager = MockQueryManager(graphs=[egf_graph])
        self.assertEqual(1, manager.count_networks())

    def test_add_graph(self):
        """Test adding a graph with insert_graph."""
        manager = MockQueryManager()
        graph = egf_graph.copy()
        manager.insert_graph(graph)
        self.assertEqual(1, manager.count_networks())
