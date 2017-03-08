# -*- coding: utf-8 -*-

import json
import logging
import os
import tempfile
import unittest

import pybel
from pybel.canonicalize import postpend_location, decanonicalize_node
from pybel.constants import GOCC_LATEST, FUNCTION, GOCC_KEYWORD, HAS_MEMBER, RELATION
from tests.constants import test_bel_simple, test_bel_extensions, mock_bel_resources, mock_parse_owl_rdf, mock_parse_owl_pybel, \
    test_bel_thorough, BelReconstitutionMixin

log = logging.getLogger('pybel')


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


class TestCanonicalize(BelReconstitutionMixin, unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, 'test.bel')

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)
        os.rmdir(self.dir)

    def canonicalize_helper(self, test_path, reconstituted=None, **kwargs):
        original = pybel.from_path(test_path, **kwargs)

        if reconstituted:
            reconstituted(original)

        with open(self.path, 'w') as f:
            pybel.to_bel(original, f)

        reloaded = pybel.from_path(self.path)

        original.namespace_url[GOCC_KEYWORD] = GOCC_LATEST

        self.assertEqual(original.document, reloaded.document)
        self.assertEqual(original.namespace_owl, reloaded.namespace_owl)
        self.assertEqual(original.namespace_url, reloaded.namespace_url)
        self.assertEqual(original.namespace_pattern, reloaded.namespace_pattern)
        self.assertEqual(original.annotation_url, reloaded.annotation_url)
        self.assertEqual(original.annotation_owl, reloaded.annotation_owl)
        self.assertEqual(original.annotation_list, reloaded.annotation_list)

        self.assertEqual(set(original.nodes()), set(reloaded.nodes()))
        self.assertEqual(set(original.edges()), set(reloaded.edges()))

        if reconstituted:
            reconstituted(reloaded)
            return

        # Really test everything is exactly the same, down to the edge data

        fmt = "Nodes with problem: {}, {}.\nOld Data:\n{}\nNew Data:\{}"
        for u, v, d in original.edges_iter(data=True):
            if d[RELATION] == HAS_MEMBER:
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
        self.canonicalize_helper(test_bel_simple, reconstituted=self.bel_simple_reconstituted)

    @mock_bel_resources
    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_canonicalize_4(self, m1, m2, m3):
        self.canonicalize_helper(test_bel_extensions)

    @mock_bel_resources
    def test_thorough(self, mock_get):
        self.canonicalize_helper(test_bel_thorough, reconstituted=self.bel_thorough_reconstituted, allow_nested=True)
