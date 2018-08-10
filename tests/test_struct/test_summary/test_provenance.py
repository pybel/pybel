# -*- coding: utf-8 -*-

"""Tests for provenance summary functions."""

import unittest

from pybel.examples import sialic_acid_graph
from pybel.struct import count_citations


class TestProvenance(unittest.TestCase):
    """Tests for provenance summary functions."""

    def test_count_citations(self):
        """Test counting citations."""
        count = count_citations(sialic_acid_graph)
        self.assertEqual(1, count)
