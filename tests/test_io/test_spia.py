# -*- coding: utf-8 -*-

"""This module contains tests for the SPIA exporter."""

import unittest

from pandas import DataFrame

from pybel.dsl import activity, composite_abundance, pmod, protein, rna
from pybel.examples.sialic_acid_example import (
    cd33, citation, evidence_1, shp1, shp2, sialic_acid_cd33_complex, sialic_acid_graph, trem2,
)
from pybel.io.spia import build_spia_matrices, get_matrix_index, to_spia_dfs, update_spia_matrices


class TestSpia(unittest.TestCase):
    """Test SPIA Exporter."""

    def setUp(self):
        self.sialic_acid_graph = sialic_acid_graph.copy()

    def test_build_matrix(self):
        """Test build empty matrix."""

        node_names = get_matrix_index(self.sialic_acid_graph)

        matrix_dict = build_spia_matrices(node_names)

        nodes = {'PTPN11', 'TREM2', 'PTPN6', 'TYROBP', 'CD33', 'SYK'}

        self.assertEqual(set(matrix_dict["activation"].columns), nodes)
        self.assertEqual(set(matrix_dict["repression"].index), nodes)

    def test_update_matrix_inhibition_ubiquination(self):
        """Test updating the matrix with an inhibition ubiquitination."""
        sub = protein(namespace='HGNC', name='A', identifier='1')
        obj = protein(namespace='HGNC', name='B', identifier='2', variants=[pmod('Ub')])

        index = {'A', 'B'}

        test_dict = {}

        test_matrix = DataFrame(0, index=index, columns=index)

        # Initialize matrix correctly
        self.assertEqual(test_matrix.values.all(), 0)

        test_dict["inhibition_ubiquination"] = test_matrix

        update_spia_matrices(test_dict, sub, obj, {'relation': 'decreases'})

        self.assertEqual(test_dict["inhibition_ubiquination"]['A']['B'], 1)
        self.assertEqual(test_dict["inhibition_ubiquination"]['A']['A'], 0)
        self.assertEqual(test_dict["inhibition_ubiquination"]['B']['A'], 0)
        self.assertEqual(test_dict["inhibition_ubiquination"]['B']['B'], 0)

    def test_update_matrix_activation_ubiquination(self):
        """Test updating the matrix with an activation ubiquitination."""
        sub = protein(namespace='HGNC', name='A', identifier='1')
        obj = protein(namespace='HGNC', name='B', identifier='2', variants=[pmod('Ub')])

        index = {'A', 'B'}

        test_dict = {}

        test_matrix = DataFrame(0, index=index, columns=index)

        test_dict["activation_ubiquination"] = test_matrix

        update_spia_matrices(test_dict, sub, obj, {'relation': 'increases'})

        self.assertEqual(test_dict["activation_ubiquination"]['A']['B'], 1)
        self.assertEqual(test_dict["activation_ubiquination"]['A']['A'], 0)
        self.assertEqual(test_dict["activation_ubiquination"]['B']['A'], 0)
        self.assertEqual(test_dict["activation_ubiquination"]['B']['B'], 0)

    def test_update_matrix_inhibition_phosphorylation(self):
        """Test updating the matrix with an inhibition phosphorylation."""
        sub = protein(namespace='HGNC', name='A', identifier='1')
        obj = protein(namespace='HGNC', name='B', identifier='2', variants=[pmod('Ph')])

        index = {'A', 'B'}

        test_dict = {}

        test_matrix = DataFrame(0, index=index, columns=index)

        test_dict["inhibition_phosphorylation"] = test_matrix

        update_spia_matrices(test_dict, sub, obj, {'relation': 'decreases'})

        self.assertEqual(test_dict["inhibition_phosphorylation"]['A']['B'], 1)
        self.assertEqual(test_dict["inhibition_phosphorylation"]['A']['A'], 0)
        self.assertEqual(test_dict["inhibition_phosphorylation"]['B']['A'], 0)
        self.assertEqual(test_dict["inhibition_phosphorylation"]['B']['B'], 0)

    def test_update_matrix_activation_phosphorylation(self):
        """Test updating the matrix with an activation phosphorylation."""

        sub = protein(namespace='HGNC', name='A', identifier='1')
        obj = protein(namespace='HGNC', name='B', identifier='2', variants=[pmod('Ph')])

        index = {'A', 'B'}

        test_dict = {}

        test_matrix = DataFrame(0, index=index, columns=index)

        test_dict["activation_phosphorylation"] = test_matrix

        update_spia_matrices(test_dict, sub, obj, {'relation': 'increases'})

        self.assertEqual(test_dict["activation_phosphorylation"]['A']['B'], 1)
        self.assertEqual(test_dict["activation_phosphorylation"]['A']['A'], 0)
        self.assertEqual(test_dict["activation_phosphorylation"]['B']['A'], 0)
        self.assertEqual(test_dict["activation_phosphorylation"]['B']['B'], 0)

    def test_update_matrix_expression(self):
        """Test updating the matrix with RNA expression."""
        sub = protein(namespace='HGNC', name='A', identifier='1')
        obj = rna(namespace='HGNC', name='B', identifier='2')

        index = {'A', 'B'}

        test_dict = {}

        test_matrix = DataFrame(0, index=index, columns=index)

        test_dict["expression"] = test_matrix

        update_spia_matrices(test_dict, sub, obj, {'relation': 'increases'})

        self.assertEqual(test_dict["expression"]['A']['B'], 1)
        self.assertEqual(test_dict["expression"]['A']['A'], 0)
        self.assertEqual(test_dict["expression"]['B']['A'], 0)
        self.assertEqual(test_dict["expression"]['B']['B'], 0)

    def test_update_matrix_repression(self):
        """Test updating the matrix with RNA repression."""
        sub = protein(namespace='HGNC', name='A', identifier='1')
        obj = rna(namespace='HGNC', name='B', identifier='2')

        index = {'A', 'B'}

        test_dict = {}

        test_matrix = DataFrame(0, index=index, columns=index)

        test_dict["repression"] = test_matrix

        update_spia_matrices(test_dict, sub, obj, {'relation': 'decreases'})

        self.assertEqual(test_dict["repression"]['A']['B'], 1)
        self.assertEqual(test_dict["repression"]['A']['A'], 0)
        self.assertEqual(test_dict["repression"]['B']['A'], 0)
        self.assertEqual(test_dict["repression"]['B']['B'], 0)

    def test_update_matrix_activation(self):
        """Test updating the matrix with activation."""
        sub = protein(namespace='HGNC', name='A', identifier='1')
        obj = protein(namespace='HGNC', name='B', identifier='2')

        index = {'A', 'B'}

        test_dict = {}

        test_matrix = DataFrame(0, index=index, columns=index)

        test_dict["activation"] = test_matrix

        update_spia_matrices(test_dict, sub, obj, {'relation': 'increases'})

        self.assertEqual(test_dict["activation"]['A']['B'], 1)
        self.assertEqual(test_dict["activation"]['A']['A'], 0)
        self.assertEqual(test_dict["activation"]['B']['A'], 0)
        self.assertEqual(test_dict["activation"]['B']['B'], 0)

    def test_update_matrix_inhibition(self):
        """Test updating the matrix with activation."""
        sub = protein(namespace='HGNC', name='A', identifier='1')
        obj = protein(namespace='HGNC', name='B', identifier='2')

        index = {'A', 'B'}

        test_dict = {}

        test_matrix = DataFrame(0, index=index, columns=index)

        test_dict["inhibition"] = test_matrix

        update_spia_matrices(test_dict, sub, obj, {'relation': 'decreases'})

        self.assertEqual(test_dict["inhibition"]['A']['B'], 1)
        self.assertEqual(test_dict["inhibition"]['A']['A'], 0)
        self.assertEqual(test_dict["inhibition"]['B']['A'], 0)
        self.assertEqual(test_dict["inhibition"]['B']['B'], 0)

    def test_update_matrix_association(self):
        """Test updating the matrix with association."""
        sub = protein(namespace='HGNC', name='A', identifier='1')
        obj = protein(namespace='HGNC', name='B', identifier='2')

        index = {'A', 'B'}

        test_dict = {}

        test_matrix = DataFrame(0, index=index, columns=index)

        test_dict["binding_association"] = test_matrix

        update_spia_matrices(test_dict, sub, obj, {'relation': 'association'})

        self.assertEqual(test_dict["binding_association"]['A']['B'], 1)
        self.assertEqual(test_dict["binding_association"]['A']['A'], 0)
        self.assertEqual(test_dict["binding_association"]['B']['A'], 0)
        self.assertEqual(test_dict["binding_association"]['B']['B'], 0)

    def test_update_matrix_pmods(self):
        """Test updating the matrix with multiple protein modifications."""
        sub = protein(namespace='HGNC', name='A', identifier='1')
        obj = protein(namespace='HGNC', name='B', identifier='2', variants=[pmod('Ub'), pmod('Ph')])

        index = {'A', 'B'}

        test_dict = {}

        test_matrix = DataFrame(0, index=index, columns=index)

        test_dict["activation_ubiquination"] = test_matrix
        test_dict["activation_phosphorylation"] = test_matrix

        update_spia_matrices(test_dict, sub, obj, {'relation': 'increases'})

        self.assertEqual(test_dict["activation_ubiquination"]['A']['B'], 1)
        self.assertEqual(test_dict["activation_ubiquination"]['A']['A'], 0)
        self.assertEqual(test_dict["activation_ubiquination"]['B']['A'], 0)
        self.assertEqual(test_dict["activation_ubiquination"]['B']['B'], 0)

        self.assertEqual(test_dict["activation_phosphorylation"]['A']['B'], 1)
        self.assertEqual(test_dict["activation_phosphorylation"]['A']['A'], 0)
        self.assertEqual(test_dict["activation_phosphorylation"]['B']['A'], 0)
        self.assertEqual(test_dict["activation_phosphorylation"]['B']['B'], 0)

    def test_spia_matrix_complexes(self):
        """Test handling of complexes."""
        self.sialic_acid_graph.add_increases(
            sialic_acid_cd33_complex,
            trem2,
            citation=citation,
            annotations={'Species': '9606', 'Confidence': 'High'},
            evidence=evidence_1,
            target_modifier=activity(),
        )

        spia_dfs = to_spia_dfs(self.sialic_acid_graph)

        self.assertEqual(spia_dfs["activation"][cd33.name][trem2.name], 1)

    def test_spia_matrix_composites(self):
        """Test handling of composites."""
        shp = composite_abundance([shp1, shp2])

        self.sialic_acid_graph.add_increases(
            shp,
            trem2,
            citation=citation,
            annotations={'Species': '9606', 'Confidence': 'High'},
            evidence=evidence_1,
            target_modifier=activity(),
        )

        spia_dfs = to_spia_dfs(self.sialic_acid_graph)

        self.assertEqual(spia_dfs["activation"][shp1.name][trem2.name], 1)
        self.assertEqual(spia_dfs["activation"][shp2.name][trem2.name], 1)
