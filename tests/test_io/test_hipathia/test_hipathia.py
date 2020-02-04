# -*- coding: utf-8 -*-

"""Tests for Hipathia."""

import tempfile
import unittest

# from pybel.examples.ampk_example import ampk_graph
# from pybel.examples.sialic_acid_example import sialic_acid_graph
# from pybel.examples.vegf_graph import vegf_graph
from pybel.io.hipathia import HipathiaConverter, make_hsa047370


class TestHipathia(unittest.TestCase):
    """Test Hipathia."""

    def test_complex(self):
        """Test that proteins in complex are all required (AND gate)."""
        # HipathiaConverter(sialic_acid_graph)

    def test_family(self):
        """Test that one or more proteins from a family are required (OR gate)."""
        # HipathiaConverter(vegf_graph)

    def test_famplex(self):
        """Test the cartesian product on a family of proteins in a complex are required."""
        # HipathiaConverter(ampk_graph)

    def test_example(self):
        """Test the stuff works for real

        1. Load example graph
        2. Export for hipathia (use temprary directory)
        3. load up correct one
        4. check the nodes are right in the ATT and SIF files (do some preprocesing to fix the names)
        """
        test_graph = make_hsa047370()
        hipathia_object = HipathiaConverter(test_graph)

        d = tempfile.TemporaryDirectory()

        # TODO: replace with d.name
        hipathia_object.output('/Users/danieldomingo/PycharmProjects/pybel/tests')

        d.cleanup()
