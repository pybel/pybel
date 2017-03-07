import logging
import unittest

import networkx as nx

from pybel.cx import to_cx_json, from_cx_json, hash_tuple
from pybel.io import from_path
from tests.constants import test_bel_thorough, BelReconstitutionMixin, test_bel_simple

log = logging.getLogger(__name__)


class TestCx(BelReconstitutionMixin, unittest.TestCase):
    def test_cx_simple(self):
        graph = from_path(test_bel_simple)
        self.bel_simple_reconstituted(graph)

        node_mapping = dict(enumerate(sorted(graph.nodes_iter(), key=hash_tuple)))

        cx = to_cx_json(graph)
        reconstituted = from_cx_json(cx)

        nx.relabel.relabel_nodes(reconstituted, node_mapping, copy=False)

        self.bel_simple_reconstituted(reconstituted, check_metadata=False)

    def test_cx_thorough(self):
        graph = from_path(test_bel_thorough, allow_nested=True)
        self.bel_thorough_reconstituted(graph)

        node_mapping = dict(enumerate(sorted(graph.nodes_iter(), key=hash_tuple)))

        cx = to_cx_json(graph)
        reconstituted = from_cx_json(cx)

        nx.relabel.relabel_nodes(reconstituted, node_mapping, copy=False)

        self.bel_thorough_reconstituted(
            reconstituted,
            check_metadata=False,
            check_warnings=False,
            check_provenance=False
        )
