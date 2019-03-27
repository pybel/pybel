# -*- coding: utf-8 -*-

"""Tests for summary functions for nodes."""

import unittest
from collections import Counter

from pybel import BELGraph
from pybel.constants import ABUNDANCE, BIOPROCESS, COMPLEX, PROTEIN
from pybel.dsl import fusion_range, pathology, protein, protein_fusion
from pybel.examples import egf_graph, sialic_acid_graph
from pybel.struct.summary.node_summary import (
    count_functions, count_names_by_namespace, count_namespaces, count_pathologies, count_variants, get_functions,
    get_names_by_namespace, get_namespaces, get_top_hubs, get_top_pathologies,
)
from pybel.testing.utils import n


class TestSummary(unittest.TestCase):
    """Test node summary functions."""

    def test_functions_sialic(self):
        """Test counting nodes and grouping by function on the sialic acid graph."""
        result = {
            PROTEIN: 7,
            COMPLEX: 1,
            ABUNDANCE: 1
        }

        self.assertEqual(set(result), get_functions(sialic_acid_graph))
        self.assertEqual(Counter(result), count_functions(sialic_acid_graph))

    def test_functions_egf(self):
        """Test counting nodes and grouping by function on the EGF graph."""
        result = {
            PROTEIN: 10,
            COMPLEX: 1,
            BIOPROCESS: 1
        }

        self.assertEqual(set(result), get_functions(egf_graph))
        self.assertEqual(result, count_functions(egf_graph))

    def test_namespaces_sialic(self):
        """Test getting and counting namespaces' contents on the sialic acid graph."""
        result = {
            'HGNC': 7,
            'CHEBI': 1
        }

        self.assertEqual(set(result), get_namespaces(sialic_acid_graph))
        self.assertEqual(Counter(result), count_namespaces(sialic_acid_graph))

    def test_namespaces_egf(self):
        """Test getting and counting namespaces' contents on the EGF graph."""
        result = {
            'HGNC': 10,
            'GO': 1,
        }

        self.assertEqual(set(result), get_namespaces(egf_graph))
        self.assertEqual(Counter(result), count_namespaces(egf_graph))

    def test_names_sialic(self):
        """Test getting and counting names by namespace."""
        result = {
            'CD33': 3,  # once as reference, once in complex, and once as variant
            'TYROBP': 1,
            'SYK': 1,
            'PTPN6': 1,
            'PTPN11': 1,
            'TREM2': 1,
        }

        self.assertEqual(set(result), get_names_by_namespace(sialic_acid_graph, 'HGNC'))
        self.assertEqual(result, dict(count_names_by_namespace(sialic_acid_graph, 'HGNC')))

    def test_names_fusions(self):
        """Test that names inside fusions are still found by the iterator."""
        graph = BELGraph()
        graph.namespace_url['HGNC'] = 'http://dummy'

        n = protein_fusion(
            partner_5p=protein(name='A', namespace='HGNC'),
            range_5p=fusion_range('p', 1, 15),
            partner_3p=protein(name='B', namespace='HGNC'),
            range_3p=fusion_range('p', 1, 100)
        )

        graph.add_node_from_data(n)

        result = {
            'A': 1,
            'B': 1,
        }

        self.assertEqual(set(result), get_names_by_namespace(graph, 'HGNC'))
        self.assertEqual(result, count_names_by_namespace(graph, 'HGNC'))

    def test_get_names_raise(self):
        """Test that an index error is raised when trying to get names from a namespace that isn't present."""
        with self.assertRaises(IndexError):
            get_names_by_namespace(sialic_acid_graph, 'NOPE')

    def test_count_names_raise(self):
        """Test that an index error is raised when trying to count a namespace that isn't present."""
        with self.assertRaises(IndexError):
            count_names_by_namespace(sialic_acid_graph, 'NOPE')

    def test_count_variants(self):
        """Test counting the number of variants in a graph."""
        variants = count_variants(sialic_acid_graph)
        self.assertEqual(1, variants['pmod'])

    def test_count_pathologies(self):
        """Test counting pathologies in the graph."""
        graph = BELGraph()
        a, b, c, d = protein(n(), n()), protein(n(), n()), pathology(n(), n()), pathology(n(), n())

        graph.add_association(a, c, citation=n(), evidence=n())
        graph.add_association(a, d, citation=n(), evidence=n())
        graph.add_association(b, d, citation=n(), evidence=n())

        pathology_counter = count_pathologies(graph)
        self.assertIn(c, pathology_counter)
        self.assertIn(d, pathology_counter)
        self.assertEqual(1, pathology_counter[c])
        self.assertEqual(2, pathology_counter[d])

        top_pathology_counter = get_top_pathologies(graph, n=1)
        self.assertEqual(1, len(top_pathology_counter))
        node, count = top_pathology_counter[0]
        self.assertEqual(d, node)
        self.assertEqual(2, count)

    def test_get_top_hubs(self):
        """Test counting pathologies in the graph."""
        graph = BELGraph()
        a, b, c = protein(n(), n()), protein(n(), n()), pathology(n(), n())

        graph.add_association(a, b, citation=n(), evidence=n())
        graph.add_association(a, c, citation=n(), evidence=n())

        top_hubs = get_top_hubs(graph, n=1)
        self.assertEqual(1, len(top_hubs))
        node, degree = top_hubs[0]
        self.assertEqual(a, node)
        self.assertEqual(2, degree)
