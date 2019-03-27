# -*- coding: utf-8 -*-

"""Test summary functions for edges."""

import unittest
from collections import Counter

from pybel import BELGraph
from pybel.dsl import protein
from pybel.examples import sialic_acid_graph
from pybel.struct.summary.edge_summary import (
    count_annotations, get_annotation_values, get_annotation_values_by_annotation, get_annotations,
    get_unused_annotations, get_unused_list_annotation_values, iter_annotation_value_pairs, iter_annotation_values,
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

        self.assertEqual({'Confidence', 'Species'}, get_annotations(sialic_acid_graph))
        self.assertEqual({'Confidence': 8, 'Species': 8}, dict(count_annotations(sialic_acid_graph)))

        annotation_values_by_annotation = get_annotation_values_by_annotation(sialic_acid_graph)
        self.assertEqual(expected, annotation_values_by_annotation)

        annotation_values = get_annotation_values(sialic_acid_graph, 'Confidence')
        self.assertEqual(expected['Confidence'], annotation_values)

    def test_get_unused_annotation_url(self):
        graph = BELGraph()
        name = n()
        graph.annotation_url[name] = n()
        self.assertEqual({name}, get_unused_annotations(graph))

    def test_get_unused_annotation_pattern(self):
        graph = BELGraph()
        name = n()
        graph.annotation_pattern[name] = n()
        self.assertEqual({name}, get_unused_annotations(graph))

    def test_get_unused_annotation_list(self):
        graph = BELGraph()
        name = n()
        graph.annotation_pattern[name] = {n(), n(), n()}
        self.assertEqual({name}, get_unused_annotations(graph))

    def test_get_unused_annotation_list_values(self):
        """Test getting unused annotation list values."""
        graph = BELGraph()
        name = 'test'
        a, b, c = 'abc'
        graph.annotation_list[name] = {a, b, c}
        graph.add_increases(protein(n(), n()), protein(n(), n()), citation=n(), evidence=n(), annotations={name: {a}})
        self.assertEqual({name: {b, c}}, get_unused_list_annotation_values(graph))
