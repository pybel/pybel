# -*- coding: utf-8 -*-

"""Tests for PyNPA."""

import unittest

import pandas as pd

from pybel import BELGraph
from pybel.dsl import ComplexAbundance, Gene, Protein, Rna
from pybel.io.pynpa import to_npa_dfs, to_npa_layers
from pybel.struct.getters import get_tf_pairs
from pybel.testing.utils import n

g1 = Gene('hgnc', '1')
r1 = Rna('hgnc', '1')
p1 = Protein('hgnc', '1')
g2 = Gene('hgnc', '2')
r2 = Rna('hgnc', '2')
p2 = Protein('hgnc', '2')
g3 = Gene('hgnc', '3')
p3 = Protein('hgnc', '3')


class TestPyNPA(unittest.TestCase):
    """Tests for PyNPA."""

    def setUp(self) -> None:
        """Set up a small test graph."""
        self.graph = BELGraph()
        self.graph.add_increases(ComplexAbundance([p1, g2]), r2, citation=n(), evidence=n())
        self.graph.add_increases(p2, p3, citation=n(), evidence=n())

    def test_get_tf_pairs(self):
        """Test getting transcription factor-target pairs."""
        tf_pairs = set(get_tf_pairs(self.graph))
        self.assertLess(0, len(tf_pairs), msg='No TF pairs pairs found')
        self.assertEqual(1, len(tf_pairs))
        example_tf, example_target, _ = list(tf_pairs)[0]
        self.assertEqual(p1, example_tf)
        self.assertEqual(r2, example_target)

    def test_export_layers(self):
        """Test that the layers are exported right."""
        ppi_layer, tf_layer = to_npa_layers(self.graph)
        self.assertIsInstance(ppi_layer, dict)
        self.assertIsInstance(tf_layer, dict)
        self.assertLess(0, len(ppi_layer), msg='PPI layer was not populated')
        self.assertLess(0, len(tf_layer), msg='TF layer was not populated')
        self.assertIn((g2, g3), ppi_layer)
        self.assertEqual(+1, ppi_layer[g2, g3])
        self.assertIn((g1, g2), tf_layer)
        self.assertEqual(+1, tf_layer[g1, g2])

    def test_export_df_curie(self):
        """Test exporting dataframes with curie-based nomenclature."""
        ppi_df, tf_df = to_npa_dfs(self.graph)
        self.assertIsInstance(ppi_df, pd.DataFrame)
        self.assertIsInstance(tf_df, pd.DataFrame)
        self.assertEqual(1, len(ppi_df.index))
        self.assertEqual(1, len(tf_df.index))
        self.assertEqual(('hgnc:2', 'hgnc:3', 1), tuple(list(ppi_df.values)[0]))
        self.assertEqual(('hgnc:1', 'hgnc:2', 1), tuple(list(tf_df.values)[0]))

    def test_export_df_name(self):
        """Test exporting dataframes with name-based nomenclature."""
        ppi_df, tf_df = to_npa_dfs(
            self.graph,
            nomenclature_method_first_layer='name',
            nomenclature_method_second_layer='name',
        )
        self.assertEqual(('2', '3', 1), tuple(list(ppi_df.values)[0]))
        self.assertEqual(('1', '2', 1), tuple(list(tf_df.values)[0]))

    def test_export_df_inode(self):
        """Test exporting dataframes with inode-based nomenclature in the second layer."""
        ppi_df, tf_df = to_npa_dfs(
            self.graph,
            nomenclature_method_first_layer='name',
            nomenclature_method_second_layer='inodes',
        )
        self.assertEqual(('2', '3', 1), tuple(list(ppi_df.values)[0]))
        self.assertEqual(('*1', '*2', 1), tuple(list(tf_df.values)[0]))
