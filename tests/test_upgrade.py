import json
import logging
import os
import tempfile
import unittest

import pybel
from pybel.canonicalize import postpend_location, decanonicalize_node
from pybel.constants import GOCC_LATEST, FUNCTION, GOCC_KEYWORD
from tests import constants
from tests.constants import test_bel, test_bel_4, mock_bel_resources

log = logging.getLogger('pybel')

pd_path = os.path.expanduser('~/dev/bms/aetionomy/parkinsons.bel')
small_corpus_path = os.path.expanduser('~/dev/bms/selventa/small_corpus.bel')


class TestCanonicalizeHelper(unittest.TestCase):
    def test_postpend_location_failure(self):
        with self.assertRaises(ValueError):
            postpend_location('', dict(name='failure'))

    def test_decanonicalize_node_failure(self):
        with self.assertRaises(ValueError):
            class NotGraph:
                node = None

            x = NotGraph()
            x.node = {'test_node': {FUNCTION: 'nope'}}

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

        original.namespace_url[GOCC_KEYWORD] = GOCC_LATEST

        self.assertEqual(original.document, reloaded.document)
        self.assertEqual(original.namespace_owl, reloaded.namespace_owl)
        self.assertEqual(original.namespace_url, reloaded.namespace_url)
        self.assertEqual(original.annotation_url, reloaded.annotation_url)
        self.assertEqual(original.annotation_list, reloaded.annotation_list)

        self.assertEqual(set(original.nodes()), set(reloaded.nodes()))
        self.assertEqual(set(original.edges()), set(reloaded.edges()))

        # Really test everything is exactly the same, down to the edge data

        fmt = "Nodes with problem: {}, {}.\nOld Data:\n{}\nNew Data:\{}"
        for u, v, d in original.edges_iter(data=True):
            if d['relation'] == 'hasMember':
                continue

            for d1 in original.edge[u][v].values():
                x = False

                for d2 in reloaded.edge[u][v].values():
                    if set(d1.keys()) == set(d2.keys()) and all(d1[k] == d2[k] for k in d1):
                        x = True

                self.assertTrue(x, msg=fmt.format(u, v, json.dumps(original.edge[u][v], indent=2, sort_keys=True),
                                                  json.dumps(reloaded.edge[u][v], indent=2, sort_keys=True)))

    @mock_bel_resources
    def test_canonicalize_1(self, mock_get):
        self.canonicalize_helper(test_bel)

    @mock_bel_resources
    @constants.mock_parse_owl_ontospy
    @constants.mock_parse_owl_pybel
    def test_canonicalize_4(self, m1, m2, m3):
        self.canonicalize_helper(test_bel_4)

    @unittest.skipUnless(os.path.exists(small_corpus_path), 'Small Corpus Missing')
    def test_small_corpus(self):
        self.maxDiff = None
        self.canonicalize_helper(small_corpus_path)

    @unittest.skipUnless(os.path.exists(pd_path), 'PD Test File Missing')
    def test_parkinsons(self):
        self.maxDiff = None
        self.canonicalize_helper(pd_path)
