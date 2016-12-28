import logging
import os
import tempfile
import unittest

import networkx as nx
from requests.exceptions import ConnectionError

import pybel
from pybel.constants import GOCC_LATEST
from pybel.parser.canonicalize import to_bel
from tests.constants import test_bel_0, test_bel_1, test_bel_3, test_bel_4

log = logging.getLogger('pybel')

pd_local_test = os.path.expanduser('~/dev/bms/aetionomy/parkinsons.bel')


class TestCanonicalize(unittest.TestCase):
    def setUp(self):
        self.tdir = tempfile.mkdtemp()

    def doCleanups(self):
        for f in os.listdir(self.tdir):
            os.remove(os.path.join(self.tdir, f))
        os.rmdir(self.tdir)

    def canonicalize_tester_helper(self, test_path):
        g_out = pybel.from_path(test_path)

        # prune isolated nodes
        g_out.remove_nodes_from(nx.isolates(g_out))

        log.info('Graph size: %s nodes, %s edges', g_out.number_of_nodes(), g_out.number_of_edges())

        tpath = os.path.join(self.tdir, 'out.bel')

        with open(tpath, 'w') as f:
            to_bel(g_out, f)

        g_in = pybel.from_path(tpath)

        os.remove(tpath)
        self.assertFalse(os.path.exists(tpath))

        g_out.namespace_url['GOCC'] = GOCC_LATEST

        self.assertEqual(g_out.document, g_in.document)
        self.assertEqual(g_out.namespace_owl, g_out.namespace_owl)
        self.assertEqual(g_out.namespace_url, g_out.namespace_url)
        self.assertEqual(g_out.annotation_url, g_out.annotation_url)
        self.assertEqual(g_out.annotation_list, g_out.annotation_list)

        self.assertEqual(set(g_out.nodes()), set(g_in.nodes()))
        self.assertEqual(set(g_out.edges()), set(g_in.edges()))

        # Really test everything is exactly the same, down to the edge data
        for u, v, d in g_out.edges_iter(data=True):
            if d['relation'] == 'hasMember':
                continue

            for d1 in g_out.edge[u][v].values():
                x = False

                for d2 in g_in.edge[u][v].values():
                    if set(d1.keys()) == set(d2.keys()) and all(d1[k] == d2[k] for k in d1):
                        x = True

                self.assertTrue(x, msg="Nodes with problem: {}, {}".format(u, v))

    def test_canonicalize_0(self):
        self.canonicalize_tester_helper(test_bel_0)

    def test_canonicalize_1(self):
        self.canonicalize_tester_helper(test_bel_1)

    def test_canonicalize_3(self):
        self.canonicalize_tester_helper(test_bel_3)

    def test_canonicalize_4(self):
        try:
            self.canonicalize_tester_helper(test_bel_4)
        except ConnectionError as e:
            log.warning('Connection error: %s', e)

    @unittest.skipUnless(os.path.exists(pd_local_test), 'Testing with SCAI data only')
    def test_canonicalize_5(self):
        self.canonicalize_tester_helper(pd_local_test)
