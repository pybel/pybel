# -*- coding: utf-8 -*-

"""Tests for Hipathia."""

import unittest

from pybel.examples.ampk_example import ampk_graph
from pybel.examples.sialic_acid_example import sialic_acid_graph
from pybel.examples.vegf_graph import vegf_graph
from pybel.io.hipathia import HipathiaConverter


class TestHipathia(unittest.TestCase):
    """Test Hipathia."""

    def test_complex(self):
        """Test that proteins in complex are all required (AND gate)."""
        HipathiaConverter(sialic_acid_graph)

    def test_family(self):
        """Test that one or more proteins from a family are required (OR gate)."""
        HipathiaConverter(vegf_graph)

    def test_famplex(self):
        """Test the cartesian product on a family of proteins in a complex are required."""
        HipathiaConverter(ampk_graph)
