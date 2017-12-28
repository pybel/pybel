# -*- coding: utf-8 -*-

import unittest

from pybel import BELGraph
from pybel.constants import *
from pybel.dsl.nodes import fusion, fusion_range, protein
from pybel.examples import egf_graph, sialic_acid_graph
from pybel.struct.summary.node_summary import (
    count_functions, count_names_by_namespace, count_namespaces, get_functions,
    get_names_by_namespace, get_namespaces,
)


class TestSummary(unittest.TestCase):
    def test_functions_sialic(self):
        result = {
            PROTEIN: 7,
            COMPLEX: 1,
            ABUNDANCE: 1
        }

        self.assertEqual(set(result), get_functions(sialic_acid_graph))
        self.assertEqual(result, count_functions(sialic_acid_graph))

    def test_functions_egf(self):
        result = {
            PROTEIN: 9,
            COMPLEX: 1,
            BIOPROCESS: 1
        }

        self.assertEqual(set(result), get_functions(egf_graph))
        self.assertEqual(result, count_functions(egf_graph))

    def test_namespaces_sialic(self):
        result = {
            'HGNC': 7,
            'CHEBI': 1
        }

        self.assertEqual(set(result), get_namespaces(sialic_acid_graph))
        self.assertEqual(result, count_namespaces(sialic_acid_graph))

    def test_namespaces_egf(self):
        result = {
            'HGNC': 9,
            'GOBP': 1,
        }

        self.assertEqual(set(result), get_namespaces(egf_graph))
        self.assertEqual(result, count_namespaces(egf_graph))

    def test_names_sialic(self):
        result = {
            'CD33': 2,
            'TYROBP': 1,
            'SYK': 1,
            'PTPN6': 1,
            'PTPN11': 1,
            'TREM2': 1,
        }

        self.assertEqual(set(result), get_names_by_namespace(sialic_acid_graph, 'HGNC'))
        self.assertEqual(result, count_names_by_namespace(sialic_acid_graph, 'HGNC'))

    def test_names_fusions(self):
        """This tests that names inside fusions are still found by the iterator"""
        graph = BELGraph()
        graph.namespace_url['HGNC'] = 'http://dummy'

        n = fusion(
            PROTEIN,
            protein(name='A', namespace='HGNC'),
            fusion_range('p', 1, 15),
            protein(name='B', namespace='HGNC'),
            fusion_range('p', 1, 100)
        )

        graph.add_node_from_data(n)

        result = {
            'A': 1,
            'B': 1,
        }

        self.assertEqual(set(result), get_names_by_namespace(graph, 'HGNC'))
        self.assertEqual(result, count_names_by_namespace(graph, 'HGNC'))

    def test_get_names_raise(self):
        with self.assertRaises(IndexError):
            get_names_by_namespace(sialic_acid_graph, 'NOPE')

    def test_count_names_raise(self):
        with self.assertRaises(IndexError):
            count_names_by_namespace(sialic_acid_graph, 'NOPE')
