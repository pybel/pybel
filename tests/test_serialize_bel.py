# -*- coding: utf-8 -*-

import unittest

from pybel import BELGraph
from pybel.canonicalize import _to_bel_lines_body
from pybel.constants import INCREASES
from pybel.dsl import *
from tests.utils import n


class TestSerializeBEL(unittest.TestCase):
    def setUp(self):
        self.citation = n()
        self.evidence = n()
        self.url = n()
        self.graph = BELGraph()
        self.graph.namespace_url['HGNC'] = self.url

    def help_check_lines(self, lines):
        """Checks the given lines match the graph built during the tests

        :type lines: list[str]
        """
        self.assertEqual(lines, list(_to_bel_lines_body(self.graph)))

    def test_simple(self):
        """Tests a scenario with a qualified edge, but no annotaitons"""
        self.graph.add_qualified_edge(
            protein(namespace='HGNC', name='YFG1'),
            protein(namespace='HGNC', name='YFG'),
            relation=INCREASES,
            citation=self.citation,
            evidence=self.evidence
        )

        self.assertEqual(2, self.graph.number_of_nodes())
        self.assertEqual(1, self.graph.number_of_edges())

        expected_lines = [
            '#' * 80,
            'SET Citation = {{"PubMed", "{}"}}'.format(self.citation),
            'SET SupportingText = "{}"'.format(self.evidence),
            'p(HGNC:YFG1) increases p(HGNC:YFG)',
            'UNSET SupportingText',
            'UNSET Citation'
        ]

        self.help_check_lines(expected_lines)

    def test_single_annotation(self):
        """Tests a scenario with a qualified edge, but no annotaitons"""
        a1, v1 = map(lambda _: n(), range(2))

        self.graph.add_qualified_edge(
            protein(namespace='HGNC', name='YFG1'),
            protein(namespace='HGNC', name='YFG'),
            relation=INCREASES,
            citation=self.citation,
            evidence=self.evidence,
            annotations={
                a1: {v1}
            }
        )

        self.assertEqual(2, self.graph.number_of_nodes())
        self.assertEqual(1, self.graph.number_of_edges())

        expected_lines = [
            '#' * 80,
            'SET Citation = {{"PubMed", "{}"}}'.format(self.citation),
            'SET SupportingText = "{}"'.format(self.evidence),
            'SET {} = "{}"'.format(a1, v1),
            'p(HGNC:YFG1) increases p(HGNC:YFG)',
            'UNSET {}'.format(a1),
            'UNSET SupportingText',
            'UNSET Citation'
        ]

        self.help_check_lines(expected_lines)

    def test_multiple_annotations(self):
        a1, v1, v2 = map(lambda _: n(), range(3))
        v1, v2 = sorted([v1, v2])

        self.graph.add_qualified_edge(
            protein(namespace='HGNC', name='YFG1'),
            protein(namespace='HGNC', name='YFG'),
            relation=INCREASES,
            citation=self.citation,
            evidence=self.evidence,
            annotations={
                a1: {v1, v2}
            }
        )

        self.assertEqual(2, self.graph.number_of_nodes())
        self.assertEqual(1, self.graph.number_of_edges())

        expected_lines = [
            '#' * 80,
            'SET Citation = {{"PubMed", "{}"}}'.format(self.citation),
            'SET SupportingText = "{}"'.format(self.evidence),
            'SET {} = {{"{}", "{}"}}'.format(a1, v1, v2),
            'p(HGNC:YFG1) increases p(HGNC:YFG)',
            'UNSET {}'.format(a1),
            'UNSET SupportingText',
            'UNSET Citation',
        ]

        self.help_check_lines(expected_lines)
