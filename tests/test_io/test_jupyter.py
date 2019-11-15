# -*- coding: utf-8 -*-

"""Test for export functions in PyBEL-Jupyter."""

import unittest

from pybel.examples import sialic_acid_graph
from pybel.io.jupyter import to_html, to_jupyter_str


class TestHTML(unittest.TestCase):
    """Text HTML functions."""

    def test_to_html(self):
        """Test export to HTML."""
        html = to_html(sialic_acid_graph)
        self.assertIsNotNone(html)

    def test_to_jupyter(self):
        """Test export to JavaScript for Jupyter."""
        javascript = to_jupyter_str(sialic_acid_graph)
        self.assertIsNotNone(javascript)
