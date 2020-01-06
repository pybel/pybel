# -*- coding: utf-8 -*-

"""Tests for the customized node-link JSON exporter (canonicalization)."""

import unittest
from tests.test_io.test_cx.examples import example_graph
from pybel import to_umbrella_nodelink_json


class TestExporter(unittest.TestCase):
    """Tests for the node-link JSON exporter."""

    def test_exporter_new_nodes(self):
        """Test new nodes created."""
        graph = example_graph.copy()

        # Check original number of nodes and edges in the example BEL Graph
        self.assertEqual(29, graph.number_of_nodes())
        self.assertEqual(29, graph.number_of_edges())

        custom_json_dict = to_umbrella_nodelink_json(graph)

        # 3 new nodes are created:
        # act(p(hgnc:MAPK1)
        # act(p(hgnc:PTK2, pmod(Ph, Tyr, 925)), ma(kin))
        # act(p(fus(hgnc:BCR, "?", hgnc:ABL1, "?")), ma(kin))
        self.assertEqual(32, len(custom_json_dict['nodes']))
        # Number of edges is maintained
        self.assertEqual(29, len(custom_json_dict['links']))
