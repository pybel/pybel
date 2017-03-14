# -*- coding: utf-8 -*-

import logging
import unittest

import pybel
from pybel.canonicalize import postpend_location, decanonicalize_node
from pybel.constants import GOCC_LATEST, FUNCTION, GOCC_KEYWORD
from tests.constants import test_bel_simple, mock_bel_resources, test_bel_thorough, BelReconstitutionMixin, \
    test_bel_isolated

log = logging.getLogger('pybel')
logging.getLogger('pybel.parser.modifiers.truncation').setLevel(50)


class TestCanonicalizeHelper(unittest.TestCase):
    def test_postpend_location_failure(self):
        with self.assertRaises(ValueError):
            postpend_location('', dict(name='failure'))

    def test_decanonicalize_node_failure(self):
        with self.assertRaises(ValueError):
            class NotGraph:
                node = None

            x = NotGraph()

            test_node = ('nope', 'nope', 'nope')
            x.node = {test_node: {FUNCTION: 'nope'}}
            decanonicalize_node(x, test_node)


class TestCanonicalize(BelReconstitutionMixin, unittest.TestCase):
    def canonicalize_helper(self, test_path, reconstituted, **kwargs):
        original = pybel.from_path(test_path, **kwargs)

        reconstituted(original)

        original_lines = pybel.to_bel_lines(original)
        reloaded = pybel.from_lines(original_lines)

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

        reconstituted(reloaded)

    @mock_bel_resources
    def test_simple(self, mock_get):
        self.canonicalize_helper(test_bel_simple, reconstituted=self.bel_simple_reconstituted)

    # @mock_bel_resources
    # @mock_parse_owl_rdf
    # @mock_parse_owl_pybel
    # def test_canonicalize_4(self, m1, m2, m3):
    #    self.canonicalize_helper(test_bel_extensions)

    @mock_bel_resources
    def test_thorough(self, mock_get):
        self.canonicalize_helper(test_bel_thorough, reconstituted=self.bel_thorough_reconstituted, allow_nested=True)

    @mock_bel_resources
    def test_isolated(self, mock_get):
        self.canonicalize_helper(test_bel_isolated, reconstituted=self.bel_isolated_reconstituted)
