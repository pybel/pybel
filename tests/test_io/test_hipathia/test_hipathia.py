# -*- coding: utf-8 -*-

"""Tests for Hipathia."""

import os
import unittest

from pybel import BELGraph
from pybel.constants import INCREASES, RELATION
from pybel.dsl import ComplexAbundance, Protein
from pybel.io.hipathia import HipathiaConverter, from_hipathia_paths, group_delimited_list

HERE = os.path.abspath(os.path.dirname(__file__))

TEST_1_ATT_PATH = os.path.join(HERE, 'test_1.att')
TEST_1_SIF_PATH = os.path.join(HERE, 'test_1.sif')

TEST_ATT_PATH = os.path.join(HERE, 'hsa04370.att')
TEST_SIF_PATH = os.path.join(HERE, 'hsa04370.sif')


class TestUtils(unittest.TestCase):
    def test_group_delimited(self):
        self.assertEqual([[5335, 5336], [9047]], group_delimited_list([5335, 5336, '/', 9047], '/'))


class TestImportHipathia(unittest.TestCase):
    """Test Hipathia import."""

    def test_import(self):
        """Test importing a hipathia network as a BEL graph."""
        graph = from_hipathia_paths(
            name='test1',
            att_path=TEST_1_ATT_PATH,
            sif_path=TEST_1_SIF_PATH,
        )
        a = Protein(namespace='ncbigene', identifier='1')
        b_family = Protein(namespace='hipathia.family', identifier='B_Family')
        b_2 = Protein(namespace='ncbigene', identifier='2')
        b_3 = Protein(namespace='ncbigene', identifier='3')
        c_family = Protein(namespace='hipathia.family', identifier='C_Family')
        c_4 = Protein(namespace='ncbigene', identifier='4')
        c_5 = Protein(namespace='ncbigene', identifier='5')
        d = Protein(namespace='ncbigene', identifier='6')
        c_d = ComplexAbundance([c_family, d])

        self.assertEqual(
            sorted({a, b_family, b_2, b_3, c_family, c_4, c_5, d, c_d}, key=str),
            sorted(graph, key=str),
        )

        self.assertIn(a, graph[c_d])  # c/d -> a
        self.assertEqual(INCREASES, list(graph[c_d][a].values())[0][RELATION])
        self.assertIn(b_family, graph[a])  # a-> b_family
        self.assertEqual(INCREASES, list(graph[a][b_family].values())[0][RELATION])


ATT_COLS = ['ID', 'label', 'genesList']


class TestExportHipathia(unittest.TestCase):
    """Test Hipathia."""

    def test_protein_activates_protein(self):
        """Test conversion of ``p(X) -> p(Y)``."""
        name = 'test'
        graph = BELGraph(name=name)
        x = Protein(namespace='ncbigene', identifier='100001', name='X')
        y = Protein(namespace='ncbigene', identifier='100002', name='Y')
        graph.add_increases(x, y, citation='', evidence='')

        converter = HipathiaConverter(graph)
        att_df = converter.get_att_df()
        att_df = att_df[ATT_COLS]
        self.assertEqual(2, len(att_df.index))

        c = [
            [f'N-{name}-1', 'X', '100001'],
            [f'N-{name}-2', 'Y', '100002'],
        ]
        self.assertEqual(c, att_df.values)

        sif_df = converter.get_sif_df()
        self.assertEqual(1, len(sif_df))
        expected_sif_df = [
            [f'N-{name}-1', 'activation', f'N-{name}-2'],
        ]
        self.assertEqual(expected_sif_df, sif_df.values)

    def test_protein_activates_family(self):
        """Test conversion of ``p(X) -> p(Y); p(Y1) isA p(Y); p(Y2) isA p(Y)``."""
        name = 'test'
        graph = BELGraph(name=name)
        x = Protein(namespace='ncbigene', identifier='100001', name='x')
        y = Protein(namespace='fplx', identifier='y_family', name='y_family')
        y1 = Protein(namespace='ncbigene', identifier='100002', name='y1')
        y2 = Protein(namespace='ncbigene', identifier='100003', name='y2')
        graph.add_increases(x, y, citation='', evidence='')
        graph.add_is_a(y1, y)
        graph.add_is_a(y2, y)

        converter = HipathiaConverter(graph)
        att_df = converter.get_att_df()
        att_df = att_df[ATT_COLS]
        self.assertEqual(2, len(att_df.index))

        c = [
            [f'N-{name}-1', 'x', '100001'],
            [f'N-{name}-2', 'y', '100002,10003'],
        ]
        self.assertEqual(c, att_df.values)

        sif_df = converter.get_sif_df()
        self.assertEqual(1, len(sif_df))
        expected_sif_df = [
            [f'N-{name}-1', 'activation', f'N-{name}-2'],
        ]
        self.assertEqual(expected_sif_df, sif_df.values)
