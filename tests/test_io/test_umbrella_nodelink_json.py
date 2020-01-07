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
        self.assertEqual(29, example_graph.number_of_edges())

        custom_json_dict = to_umbrella_nodelink(example_graph)

        # 3 new nodes are created:
        # act(p(hgnc:MAPK1)
        # act(p(hgnc:PTK2, pmod(Ph, Tyr, 925)), ma(kin))
        # act(p(fus(hgnc:BCR, "?", hgnc:ABL1, "?")), ma(kin))
        self.assertEqual(32, len(custom_json_dict['nodes']))

        # TODO test for these nodes actually being in the nodes list

        # Number of edges is maintained
        self.assertEqual(29, len(custom_json_dict['links']))

        # TODO test some actual edges being in the edge list
