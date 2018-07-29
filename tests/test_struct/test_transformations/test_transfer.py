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
        children = list(iter_children(statin_graph, hmgcr_inhibitor.as_tuple()))

        self.assertNotEqual(0, len(children), msg='no children found')
        self.assertIn(mevinolinic_acid.as_tuple(), children, msg='direct child not found')

    def test_infer(self):
        """Test inferring child relations."""
        graph = statin_graph.copy()
        self.assertEqual(9, graph.number_of_nodes())
        self.assertEqual(8, graph.number_of_edges())

        self.assertNotIn(ec_11134.as_tuple(), graph.edge[fluvastatin.as_tuple()])
        self.assertNotIn(ec_11188.as_tuple(), graph.edge[fluvastatin.as_tuple()])
        self.assertNotIn(ec_11134.as_tuple(), graph.edge[avorastatin.as_tuple()])
        self.assertNotIn(ec_11188.as_tuple(), graph.edge[avorastatin.as_tuple()])
        self.assertNotIn(ec_11134.as_tuple(), graph.edge[synthetic_statin.as_tuple()])
        self.assertNotIn(ec_11188.as_tuple(), graph.edge[synthetic_statin.as_tuple()])
        self.assertNotIn(ec_11134.as_tuple(), graph.edge[statin.as_tuple()])
        self.assertNotIn(ec_11188.as_tuple(), graph.edge[statin.as_tuple()])
        self.assertNotIn(ec_11134.as_tuple(), graph.edge[mevinolinic_acid.as_tuple()])
        self.assertNotIn(ec_11188.as_tuple(), graph.edge[mevinolinic_acid.as_tuple()])
        self.assertIn(ec_11134.as_tuple(), graph.edge[hmgcr_inhibitor.as_tuple()])
        self.assertIn(ec_11188.as_tuple(), graph.edge[hmgcr_inhibitor.as_tuple()])

        infer_child_relations(graph, hmgcr_inhibitor)

        self.assertIn(ec_11134.as_tuple(), graph.edge[fluvastatin.as_tuple()])
        self.assertIn(ec_11188.as_tuple(), graph.edge[fluvastatin.as_tuple()])
        self.assertIn(ec_11134.as_tuple(), graph.edge[avorastatin.as_tuple()])
        self.assertIn(ec_11188.as_tuple(), graph.edge[avorastatin.as_tuple()])
        self.assertIn(ec_11134.as_tuple(), graph.edge[synthetic_statin.as_tuple()])
        self.assertIn(ec_11188.as_tuple(), graph.edge[synthetic_statin.as_tuple()])
        self.assertIn(ec_11134.as_tuple(), graph.edge[statin.as_tuple()])
        self.assertIn(ec_11188.as_tuple(), graph.edge[statin.as_tuple()])
        self.assertIn(ec_11134.as_tuple(), graph.edge[mevinolinic_acid.as_tuple()])
        self.assertIn(ec_11188.as_tuple(), graph.edge[mevinolinic_acid.as_tuple()])
        self.assertIn(ec_11134.as_tuple(), graph.edge[hmgcr_inhibitor.as_tuple()])
        self.assertIn(ec_11188.as_tuple(), graph.edge[hmgcr_inhibitor.as_tuple()])

        self.assertEqual(9, graph.number_of_nodes())
        self.assertEqual(18, graph.number_of_edges())

        infer_child_relations(graph, ec_11134)

        self.assertIn(hmgcr.as_tuple(), graph.edge[fluvastatin.as_tuple()])
        self.assertIn(hmgcr.as_tuple(), graph.edge[avorastatin.as_tuple()])
        self.assertIn(hmgcr.as_tuple(), graph.edge[synthetic_statin.as_tuple()])
        self.assertIn(hmgcr.as_tuple(), graph.edge[statin.as_tuple()])
        self.assertIn(hmgcr.as_tuple(), graph.edge[mevinolinic_acid.as_tuple()])
        self.assertIn(hmgcr.as_tuple(), graph.edge[hmgcr_inhibitor.as_tuple()])

        self.assertEqual(9, graph.number_of_nodes())
        self.assertEqual(24, graph.number_of_edges())

        self.assertEqual(9, statin_graph.number_of_nodes(), msg='original graph nodes should not be modified')
        self.assertEqual(8, statin_graph.number_of_edges(), msg='original graph edges should not be modified')

    @unittest.skip('not yet sure if this is necessary')
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
