import logging
import os
import tempfile
import unittest

import pybel
from pybel.canonicalize import decanonicalize_variant, postpend_location, decanonicalize_node
from pybel.constants import GOCC_LATEST
from tests import constants
from tests.constants import test_bel, test_bel_4, mock_bel_resources

log = logging.getLogger('pybel')


class TestCanonicalizeHelper(unittest.TestCase):
    def test_postpend_location_failure(self):
        with self.assertRaises(ValueError):
            postpend_location('', dict(name='failure'))

    def test_decanonicalize_variant_failure(self):
        with self.assertRaises(ValueError):
            decanonicalize_variant('rmod(lol)')

    def test_decanonicalize_node_failure(self):
        with self.assertRaises(ValueError):
            class NotGraph:
                node = None

            x = NotGraph()
            x.node = {'test_node': {'type': 'nope'}}

            decanonicalize_node(x, 'test_node')


class TestCanonicalize(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, 'test.bel')

    def tearDown(self):
        os.remove(self.path)
        os.rmdir(self.dir)

    def canonicalize_helper(self, test_path):
        original = pybel.from_path(test_path)

        with open(self.path, 'w') as f:
            pybel.to_bel(original, f)

        reloaded = pybel.from_path(self.path)

        original.namespace_url['GOCC'] = GOCC_LATEST

        self.assertEqual(original.document, reloaded.document)
        self.assertEqual(original.namespace_owl, reloaded.namespace_owl)
        self.assertEqual(original.namespace_url, reloaded.namespace_url)
        self.assertEqual(original.annotation_url, reloaded.annotation_url)
        self.assertEqual(original.annotation_list, reloaded.annotation_list)

        self.assertEqual(set(original.nodes()), set(reloaded.nodes()))
        self.assertEqual(set(original.edges()), set(reloaded.edges()))

        # Really test everything is exactly the same, down to the edge data
        for u, v, d in original.edges_iter(data=True):
            if d['relation'] == 'hasMember':
                continue

            for d1 in original.edge[u][v].values():
                x = False

                for d2 in reloaded.edge[u][v].values():
                    if set(d1.keys()) == set(d2.keys()) and all(d1[k] == d2[k] for k in d1):
                        x = True

                self.assertTrue(x, msg="Nodes with problem: {}, {}".format(u, v))

    @mock_bel_resources
    def test_canonicalize_1(self, mock_get):
        self.canonicalize_helper(test_bel)

    @mock_bel_resources
    @constants.mock_parse_owl_ontospy
    @constants.mock_parse_owl_pybel
    def test_canonicalize_4(self, m1, m2, m3):
        self.canonicalize_helper(test_bel_4)
