# -*- coding: utf-8 -*-

"""Tests for provenance summary functions."""

import unittest

from pybel.examples import sialic_acid_graph


class TestProvenance(unittest.TestCase):
    """Tests for provenance summary functions."""

    def test_count_citations(self):
        """Test counting citations."""
        count = sialic_acid_graph.number_of_citations()
        self.assertEqual(1, count)
