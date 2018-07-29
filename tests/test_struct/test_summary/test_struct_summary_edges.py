# -*- coding: utf-8 -*-

"""Test summary functions for edges."""

from collections import Counter
import unittest

from pybel import BELGraph
from pybel.dsl import protein
from pybel.examples import sialic_acid_graph
from pybel.struct.summary.edge_summary import (
    get_annotation_values, get_annotation_values_by_annotation, iter_annotation_value_pairs, iter_annotation_values,
)
from pybel.testing.utils import n


class TestEdgeSummary(unittest.TestCase):
    """Test summary functions for edges."""

    def test_1(self):
        """Test iterating over annotation/value pairs."""
        graph = BELGraph()
        u = protein('HGNC', name='U')
        v = protein('HGNC', name='V')
        w = protein('HGNC', name='W')

        graph.add_increases(
            u,
            v,
            evidence=n(),
            citation=n(),
            annotations={
                'A': {'1', '2'},
                'B': {'X'}
            }
        )

        graph.add_increases(
            u,
            w,
            evidence=n(),
            citation=n(),
            annotations={
                'A': {'1', '3'},
                'C': {'a'}
            }
        )

        graph.add_increases(
            w,
            v,
            evidence=n(),
            citation=n(),
        )

        x = dict(Counter(iter_annotation_value_pairs(graph)))

        self.assertEqual({
            ('A', '1'): 2,
            ('A', '2'): 1,
            ('A', '3'): 1,
            ('B', 'X'): 1,
            ('C', 'a'): 1,
        }, x)

        y = Counter(iter_annotation_values(graph, 'A'))
        self.assertEqual(x['A', '1'] + x['A', '2'] + x['A', '3'], sum(y.values()))

        y = Counter(iter_annotation_values(graph, 'B'))
        self.assertEqual(x['B', 'X'], sum(y.values()))

        y = Counter(iter_annotation_values(graph, 'C'))
        self.assertEqual(x['C', 'a'], sum(y.values()))

    def test_get_annotation_values(self):
        """Test getting annotation values."""
        expected = {
            'Confidence': {'High', 'Low'},
            'Species': {'9606'}
        }
        annotation_values_by_annotation = get_annotation_values_by_annotation(sialic_acid_graph)
        self.assertEqual(expected, annotation_values_by_annotation)

        annotation_values = get_annotation_values(sialic_acid_graph, 'Confidence')
        self.assertEqual(expected['Confidence'], annotation_values)
