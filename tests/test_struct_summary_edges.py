# -*- coding: utf-8 -*-

import unittest
from collections import Counter

from pybel import BELGraph
from pybel.constants import INCREASES
from pybel.dsl import protein
from pybel.examples import sialic_acid_graph
from pybel.struct.summary.edge_summary import get_annotation_values_by_annotation, iter_annotation_values


class TestEdgeSummary(unittest.TestCase):
    def test_1(self):
        graph = BELGraph()
        u = protein('HGNC', name='U')
        v = protein('HGNC', name='V')
        w = protein('HGNC', name='W')

        graph.add_qualified_edge(
            u,
            v,
            relation=INCREASES,
            evidence='',
            citation='',
            annotations={
                'A': {'1', '2'},
                'B': {'X'}
            }
        )

        graph.add_qualified_edge(
            u,
            w,
            relation=INCREASES,
            evidence='',
            citation='',
            annotations={
                'A': {'1', '3'},
                'C': {'a'}
            }
        )

        graph.add_qualified_edge(
            w,
            v,
            relation=INCREASES,
            evidence='',
            citation='',
        )

        x = dict(Counter(iter_annotation_values(graph)))

        self.assertEqual({
            ('A', '1'): 2,
            ('A', '2'): 1,
            ('A', '3'): 1,
            ('B', 'X'): 1,
            ('C', 'a'): 1,
        }, x)

    def test_get_annotation_values(self):
        expected = {
            'Confidence': {'High', 'Low'},
            'Species': {'9606'}
        }
        result = get_annotation_values_by_annotation(sialic_acid_graph)
        self.assertEqual(expected, result)
