# -*- coding: utf-8 -*-

"""Tests for ``pybel.tokens``."""

import unittest

from pybel.constants import ABUNDANCE, FUNCTION, IDENTIFIER, NAME, NAMESPACE
from pybel.dsl import Abundance
from pybel.testing.utils import n
from pybel.tokens import _simple_po_to_dict


class TestRecover(unittest.TestCase):
    """Test converting dictionaries to DSL."""

    def test_simple(self):
        """Test converting a simple dictionary."""
        namespace, name, identifier = n(), n(), n()

        self.assertEqual(
            Abundance(namespace=namespace, name=name),
            _simple_po_to_dict({
                FUNCTION: ABUNDANCE,
                NAMESPACE: namespace,
                NAME: name,
            })
        )

        self.assertEqual(
            Abundance(namespace=namespace, name=name, identifier=identifier),
            _simple_po_to_dict({
                FUNCTION: ABUNDANCE,
                NAMESPACE: namespace,
                NAME: name,
                IDENTIFIER: identifier,
            })
        )

        self.assertEqual(
            Abundance(namespace=namespace, identifier=identifier),
            _simple_po_to_dict({
                FUNCTION: ABUNDANCE,
                NAMESPACE: namespace,
                IDENTIFIER: identifier,
            })
        )

        with self.assertRaises(ValueError):
            _simple_po_to_dict({
                FUNCTION: ABUNDANCE,
                NAMESPACE: namespace,
            })
