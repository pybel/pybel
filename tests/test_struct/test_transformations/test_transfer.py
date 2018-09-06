# -*- coding: utf-8 -*-

"""Tests for transfer of knowledge and inference functions."""

import unittest

from pybel.examples.statin_example import (
    avorastatin, ec_11134, ec_11188, fluvastatin, hmgcr, hmgcr_inhibitor, mevinolinic_acid, statin, statin_graph,
    synthetic_statin,
)
from pybel.struct.mutation import infer_child_relations
from pybel.struct.mutation.transfer import iter_children


class TestTransfer(unittest.TestCase):
    """Tests for transfer of knowledge and inference functions."""

    def test_get_children(self):
        """Test iterating over the children of a node."""
        children = list(iter_children(statin_graph, hmgcr_inhibitor))

        self.assertNotEqual(0, len(children), msg='no children found')
        self.assertIn(mevinolinic_acid, children, msg='direct child not found')

    def test_infer(self):
        """Test inferring child relations."""
        graph = statin_graph.copy()
        self.assertEqual(9, graph.number_of_nodes())
        self.assertEqual(8, graph.number_of_edges())

        self.assertNotIn(ec_11134, graph[fluvastatin])
        self.assertNotIn(ec_11188, graph[fluvastatin])
        self.assertNotIn(ec_11134, graph[avorastatin])
        self.assertNotIn(ec_11188, graph[avorastatin])
        self.assertNotIn(ec_11134, graph[synthetic_statin])
        self.assertNotIn(ec_11188, graph[synthetic_statin])
        self.assertNotIn(ec_11134, graph[statin])
        self.assertNotIn(ec_11188, graph[statin])
        self.assertNotIn(ec_11134, graph[mevinolinic_acid])
        self.assertNotIn(ec_11188, graph[mevinolinic_acid])
        self.assertIn(ec_11134, graph[hmgcr_inhibitor])
        self.assertIn(ec_11188, graph[hmgcr_inhibitor])

        infer_child_relations(graph, hmgcr_inhibitor)

        self.assertIn(ec_11134, graph[fluvastatin])
        self.assertIn(ec_11188, graph[fluvastatin])
        self.assertIn(ec_11134, graph[avorastatin])
        self.assertIn(ec_11188, graph[avorastatin])
        self.assertIn(ec_11134, graph[synthetic_statin])
        self.assertIn(ec_11188, graph[synthetic_statin])
        self.assertIn(ec_11134, graph[statin])
        self.assertIn(ec_11188, graph[statin])
        self.assertIn(ec_11134, graph[mevinolinic_acid])
        self.assertIn(ec_11188, graph[mevinolinic_acid])
        self.assertIn(ec_11134, graph[hmgcr_inhibitor])
        self.assertIn(ec_11188, graph[hmgcr_inhibitor])

        self.assertEqual(9, graph.number_of_nodes())
        self.assertEqual(18, graph.number_of_edges())

        infer_child_relations(graph, ec_11134)

        self.assertIn(hmgcr, graph[fluvastatin])
        self.assertIn(hmgcr, graph[avorastatin])
        self.assertIn(hmgcr, graph[synthetic_statin])
        self.assertIn(hmgcr, graph[statin])
        self.assertIn(hmgcr, graph[mevinolinic_acid])
        self.assertIn(hmgcr, graph[hmgcr_inhibitor])

        self.assertEqual(9, graph.number_of_nodes())
        self.assertEqual(24, graph.number_of_edges())

        self.assertEqual(9, statin_graph.number_of_nodes(), msg='original graph nodes should not be modified')
        self.assertEqual(8, statin_graph.number_of_edges(), msg='original graph edges should not be modified')

    def test_does_not_redo(self):
        """Test that :func:`propagate_node_relations` does not add the same edges twice."""
        graph = statin_graph.copy()
        self.assertEqual(9, graph.number_of_nodes())
        self.assertEqual(8, graph.number_of_edges())

        infer_child_relations(graph, hmgcr_inhibitor)
        self.assertEqual(9, graph.number_of_nodes())
        self.assertEqual(18, graph.number_of_edges())

        infer_child_relations(graph, hmgcr_inhibitor)
        self.assertEqual(9, graph.number_of_nodes())
        self.assertEqual(18, graph.number_of_edges(), msg='edges should not be added again')


if __name__ == '__main__':
    unittest.main()
