# -*- coding: utf-8 -*-

"""Tests for getters."""

import unittest

from pybel import BELGraph
from pybel.dsl import ComplexAbundance, Protein, Rna
from pybel.struct.getters import get_tf_pairs
from pybel.testing.utils import n


def _tf_up(graph, protein, rna):
    graph.add_directly_increases(
        ComplexAbundance([protein, rna.get_gene()]),
        rna,
        citation=n(),
        evidence=n(),
    )


def _tf_down(graph, protein, rna):
    graph.add_directly_decreases(
        ComplexAbundance([protein, rna.get_gene()]),
        rna,
        citation=n(),
        evidence=n(),
    )


def _bel_pair_key(k):
    return tuple(map(str, k))


class TestGetters(unittest.TestCase):
    """Tests for getters."""

    def test_get_tf_pairs(self):
        """Test iterating over transcription factor pairs."""
        graph = BELGraph()
        p1, p2, p3 = (Protein('test', str(i)) for i in range(1, 4))
        r4, r5, r6 = (Rna('test', str(j)) for j in range(4, 7))

        g4 = r4.get_gene()
        self.assertIsNotNone(g4)
        g5 = r5.get_gene()
        self.assertIsNotNone(g5)

        c14, c25 = ComplexAbundance([p1, g4]), ComplexAbundance([p2, g5])
        _tf_up(graph, p1, r4)
        _tf_down(graph, p2, r5)
        graph.add_correlation(p3, r6, citation=n(), evidence=n())

        self.assertEqual({p1, p2, p3, r4, r5, r6, g4, g5, c14, c25}, set(graph))

        expected_edges = [
            (c14, r4), (p1, c14), (g4, c14),
            (c25, r5), (p2, c25), (g5, c25),
            (p3, r6), (r6, p3),
        ]
        sorted_expected_edges = sorted(expected_edges, key=_bel_pair_key)
        sorted_actual_edges = sorted(graph.edges(), key=_bel_pair_key)

        self.assertEqual(sorted_expected_edges, sorted_actual_edges)

        pairs = set(get_tf_pairs(graph))
        expected_pairs = {(p1, r4, +1), (p2, r5, -1)}
        self.assertEqual(expected_pairs, pairs)
