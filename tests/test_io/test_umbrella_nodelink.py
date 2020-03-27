# -*- coding: utf-8 -*-

"""Tests for the umbrella node-link JSON exporter."""

import unittest

from pybel.io.umbrella_nodelink import to_umbrella_nodelink
from tests.test_io.test_cx.examples import example_graph


class TestUmbrellaNodeLinkExporter(unittest.TestCase):
    """Tests for the umbrella node-link JSON exporter."""

    def test_exporter_new_nodes(self):
        """Test new nodes created."""
        # Check original number of nodes and edges in the example BEL Graph
        self.assertEqual(29, example_graph.number_of_nodes())
        self.assertEqual(32, example_graph.number_of_edges())

        custom_json_dict = to_umbrella_nodelink(example_graph)

        self.assertEqual(32, len(custom_json_dict['nodes']))

        # 3 new nodes are created:
        self.assertIn("act(p(hgnc:MAPK1), ma(kin))", custom_json_dict['nodes'])
        self.assertIn("act(p(hgnc:PTK2, pmod(Ph, Tyr, 925)), ma(kin))", custom_json_dict['nodes'])
        self.assertIn('act(p(fus(hgnc:BCR, "?", hgnc:ABL1, "?")), ma(kin))', custom_json_dict['nodes'])

    def test_exporter_edges(self):
        """Test no new edges created."""
        # Check original number of nodes and edges in the example BEL Graph
        self.assertEqual(29, example_graph.number_of_nodes(), msg='Wrong number of nodes')
        self.assertEqual(32, example_graph.number_of_edges(), msg='Wrong number of edges')

        custom_json_dict = to_umbrella_nodelink(example_graph)

        # Number of edges is maintained
        self.assertEqual(32, len(custom_json_dict['links']), msg='Wrong number of links in Umbrella JSON')
