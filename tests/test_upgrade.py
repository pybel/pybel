# -*- coding: utf-8 -*-

import logging
import unittest

from pybel import from_path, to_bel_lines, from_lines
from pybel.canonicalize import postpend_location, decanonicalize_node
from pybel.constants import GOCC_LATEST, FUNCTION, GOCC_KEYWORD
from tests.constants import TemporaryCacheMixin, BelReconstitutionMixin
from tests.constants import test_bel_simple, mock_bel_resources, test_bel_thorough, test_bel_isolated

log = logging.getLogger('pybel')
logging.getLogger('pybel.parser.modifiers.truncation').setLevel(50)


class TestCanonicalizeHelper(unittest.TestCase):
    def test_postpend_location_failure(self):
        with self.assertRaises(ValueError):
            postpend_location('', dict(name='failure'))

    def test_decanonicalize_node_failure(self):
        class NotGraph:
            node = None

        x = NotGraph()

        test_node = ('nope', 'nope', 'nope')
        x.node = {test_node: {FUNCTION: 'nope'}}

        with self.assertRaises(ValueError):
            decanonicalize_node(x, test_node)


class TestCanonicalize(TemporaryCacheMixin, BelReconstitutionMixin):
    def canonicalize_helper(self, test_path, reconstituted, allow_nested=False):
        original = from_path(test_path, manager=self.manager, allow_nested=allow_nested)
        reconstituted(original)
        original_lines = to_bel_lines(original)
        reloaded = from_lines(original_lines, manager=self.manager)
        original.namespace_url[GOCC_KEYWORD] = GOCC_LATEST
        reconstituted(reloaded)

    @mock_bel_resources
    def test_simple(self, mock_get):
        self.canonicalize_helper(test_bel_simple, reconstituted=self.bel_simple_reconstituted)

    @mock_bel_resources
    def test_thorough(self, mock_get):
        self.canonicalize_helper(test_bel_thorough, reconstituted=self.bel_thorough_reconstituted, allow_nested=True)

    @mock_bel_resources
    def test_isolated(self, mock_get):
        self.canonicalize_helper(test_bel_isolated, reconstituted=self.bel_isolated_reconstituted)
