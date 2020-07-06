# -*- coding: utf-8 -*-

"""Tests for Hipathia export."""

import unittest
from typing import Tuple

import pandas as pd

from pybel import BELGraph
from pybel.dsl import ComplexAbundance, Protein
from pybel.io.hipathia import ATT_COLS, to_hipathia_dfs
from pybel.testing.utils import n

PROTEIN_NAMESPACE = 'ncbigene'
FAMILY_NAMESPACE = 'hipathia.family'
a = Protein(namespace='ncbigene', identifier='P001', name='A')
b_family = Protein(namespace='hipathia.family', identifier='F001', name='B_Family')
b1 = Protein(namespace='ncbigene', identifier='P002', name='B1')
b2 = Protein(namespace='ncbigene', identifier='P003', name='B2')
c_family = Protein(namespace='hipathia.family', identifier='F002', name='C_Family')
c1 = Protein(namespace='ncbigene', identifier='P004', name='C1')
c2 = Protein(namespace='ncbigene', identifier='P005', name='C2')
d = Protein(namespace='ncbigene', identifier='P006', name='D')
c_d = ComplexAbundance([c_family, d])
e = Protein(namespace='ncbigene', identifier='P007', name='E')
f = Protein(namespace='ncbigene', identifier='P008', name='F')
e_f = ComplexAbundance([e, f])

name = 'test'


class TestExportHipathia(unittest.TestCase):
    """Test Hipathia."""

    def setUp(self) -> None:
        self.graph = BELGraph(name=name)

    def _get_dfs(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        return to_hipathia_dfs(self.graph)

    def test_protein_activates_protein(self):
        """Test conversion of ``p(A) -> p(D)``."""
        self.graph.add_increases(a, d, citation=n(), evidence='')

        att_df, sif_df = self._get_dfs()

        att_df = att_df[ATT_COLS]
        self.assertEqual(2, len(att_df.index))
        self.assertEqual(
            [
                ['N-{name}-1'.format(name=name), a.name, a.identifier],
                ['N-{name}-2'.format(name=name), d.name, d.identifier],
            ],
            att_df.values.tolist(),
        )

        self.assertEqual(1, len(sif_df))
        self.assertEqual(
            [
                ['N-{name}-1'.format(name=name), 'activation', 'N-{name}-2'.format(name=name)],
            ],
            sif_df.values.tolist(),
        )

    def test_protein_activates_family(self):
        """Test conversion of ``p(A) -> p(B); p(B1) isA p(B); p(B2) isA p(B)``."""
        self.graph.add_increases(a, b_family, citation=n(), evidence=n())
        self.graph.add_is_a(b1, b_family)
        self.graph.add_is_a(b2, b_family)

        att_df, sif_df = self._get_dfs()

        att_df = att_df[ATT_COLS]
        self.assertEqual(2, len(att_df.index))
        self.assertEqual(
            [
                ['N-{name}-1'.format(name=name), b_family.name, ','.join((b1.identifier, b2.identifier))],
                ['N-{name}-2'.format(name=name), a.name, a.identifier],
            ],
            att_df.values.tolist(),
        )

        self.assertEqual(1, len(sif_df))
        self.assertEqual(
            [
                ['N-{name}-2'.format(name=name), 'activation', 'N-{name}-1'.format(name=name)],
            ],
            sif_df.values.tolist(),
        )

    def test_protein_activates_complex_proteins(self):
        """Test conversion of ``p(A) -> complex(p(E), p(F))``."""
        self.graph.add_increases(a, e_f, citation=n(), evidence='')

        att_df, sif_df = self._get_dfs()

        att_df = att_df[ATT_COLS]
        self.assertEqual(2, len(att_df.index))
        self.assertEqual(
            [
                ['N-{name}-1 2'.format(name=name), ' '.join((e.name, f.name)),
                 '{},/,{}'.format(e.identifier, f.identifier)],
                ['N-{name}-3'.format(name=name), a.name, a.identifier],
            ],
            att_df.values.tolist(),
        )

        self.assertEqual(1, len(sif_df))
        self.assertEqual(
            [
                ['N-{name}-3'.format(name=name), 'activation', 'N-{name}-1 2'.format(name=name)],
            ],
            sif_df.values.tolist(),
        )

    def test_protein_activates_complex_mixed(self):
        """Test conversion of ``p(A) -> complex(p(E), p(B))`` when b is a family."""
        self.graph.add_increases(a, e_f, citation=n(), evidence='')

        att_df, sif_df = self._get_dfs()

        att_df = att_df[ATT_COLS]
        self.assertEqual(2, len(att_df.index))
        self.assertEqual(
            [
                ['N-{name}-1 2'.format(name=name),
                 ' '.join((e.name, f.name)),
                 '{},/,{}'.format(e.identifier, f.identifier)],
                ['N-{name}-3'.format(name=name), a.name, a.identifier],
            ],
            att_df.values.tolist(),
        )

        self.assertEqual(1, len(sif_df))
        self.assertEqual(
            [
                ['N-{name}-3'.format(name=name), 'activation', 'N-{name}-1 2'.format(name=name)],
            ],
            sif_df.values.tolist(),
        )
