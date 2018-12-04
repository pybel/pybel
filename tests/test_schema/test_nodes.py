# -*- coding: utf-8 -*-

"""Unit tests for validating DSL nodes."""

import unittest

from pybel.constants import NAME, NAMESPACE, FUNCTION, VARIANTS, KIND
from pybel.dsl import Protein, ProteinModification
from pybel.schema import validate_node

n1 = Protein('HGNC', 'YFG', )
n2 = Protein('HGNC', 'YFG', variants=ProteinModification('Ph'))


class TestNodeSchema(unittest.TestCase):
    """Tests for the PyBEL node validator."""

    def test_simple(self):
        """Test validating simple namespace/name nodes."""
        self.assertTrue(validate_node(n1), msg="Valid protein, should be validated by schema")

    def test_simple_fail(self):
        """Test validating simple namespace/name nodes."""
        self.assertFalse(validate_node({
            NAMESPACE: 'HGNC',
            NAME: 'YFG',
        }), msg='Invalid object, should not be validated')

    def test_protein_with_modification(self):
        """Test validating a protein with modifications."""
        self.assertTrue(validate_node(n2), msg="Valid protein, should be validated by schema")

    def test_protein_with_modification_fail(self):
        """Test invalidating a protein with modifications that are incorrect"""
        test_protein = {
            FUNCTION: 'protein',
            NAMESPACE: 'HGNC',
            NAME: 'YFG',
            VARIANTS: [
                {
                    #KIND: 'pmod'
                }
            ]
        }
        self.assertFalse(validate_node(test_protein), msg="Invalid protein with modifications, should not be validated by schema")
