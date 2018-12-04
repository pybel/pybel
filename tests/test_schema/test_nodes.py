# -*- coding: utf-8 -*-

"""Unit tests for validating DSL nodes."""

import unittest

from pybel.constants import NAME, NAMESPACE
from pybel.dsl import Protein, ProteinModification
from pybel.schema import validate_node

n1 = Protein('HGNC', 'YFG')
n2 = Protein('HGNC', 'YFG', variants=ProteinModification('Ph'))


class TestNodeSchema(unittest.TestCase):
    """Tests for the PyBEL node validator."""

    def test_simple(self):
        """Test validating simple namespace/name nodes."""
        self.assertTrue(validate_node(n1))

    def test_simple_fail(self):
        """Test validating simple namespace/name nodes."""
        self.assertFalse(validate_node({
            NAMESPACE: 'HGNC',
            NAME: 'YFG',
        }))

    def test_protein_with_modification(self):
        """Test validating a protein with modifications."""
        self.assertTrue(validate_node(n2))
