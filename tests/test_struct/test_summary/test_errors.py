# -*- coding: utf-8 -*-

"""Tests for :mod:`pybel.struct.summary.errors`."""

import unittest

from pybel import BELGraph
from pybel.parser.exc import NakedNameWarning, UndefinedAnnotationWarning
from pybel.struct.summary import count_error_types, count_naked_names, get_naked_names
from pybel.testing.utils import n


class TestErrors(unittest.TestCase):
    """Test :mod:`pybel.struct.summary.errors`."""

    def test_count_error_types(self):
        """Test counting error types."""
        graph = BELGraph()

        line_number = 30
        position = 4
        line = n()
        annotation = n()

        exc = UndefinedAnnotationWarning(
            line_number=line_number,
            line=line,
            position=position,
            annotation=annotation,
        )

        graph.add_warning(exc)

        error_types = count_error_types(graph)

        self.assertEqual(1, len(error_types))
        self.assertIn(UndefinedAnnotationWarning.__name__, error_types)
        self.assertEqual(1, error_types[UndefinedAnnotationWarning.__name__])

    def test_get_naked_names(self):
        """Retrieve the naked names from a graph."""
        graph = BELGraph()

        n_names = 5

        line_number = 30
        position = 4
        line = n()

        names = {n() for _ in range(n_names)}

        exceptions = [
            NakedNameWarning(
                line_number=line_number,
                line=line,
                position=position,
                name=name,
            )
            for name in names
        ]

        for exception in exceptions:
            graph.add_warning(exception=exception)

        graph.add_warning(exception=exceptions[0])

        self.assertEqual(6, graph.number_of_warnings())

        naked_names = get_naked_names(graph)
        self.assertEqual(names, naked_names)

        naked_name_counter = count_naked_names(graph)
        self.assertEqual(n_names, len(naked_name_counter))
        self.assertEqual(2, naked_name_counter[exceptions[0].name])
