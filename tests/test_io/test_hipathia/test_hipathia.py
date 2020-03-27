# -*- coding: utf-8 -*-

"""Tests for Hipathia."""

import os
import tempfile
import unittest

from pybel.constants import INCREASES, RELATION
from pybel.dsl import ComplexAbundance, Protein
from pybel.io.hipathia import HipathiaConverter, from_hipathia_paths, group_delimited_list, make_hsa047370

HERE = os.path.abspath(os.path.dirname(__file__))

TEST_1_ATT_PATH = os.path.join(HERE, 'test_1.att')
TEST_1_SIF_PATH = os.path.join(HERE, 'test_1.sif')

TEST_ATT_PATH = os.path.join(HERE, 'hsa04370.att')
TEST_SIF_PATH = os.path.join(HERE, 'hsa04370.sif')


# from pybel.examples.ampk_example import ampk_graph
# from pybel.examples.sialic_acid_example import sialic_acid_graph
# from pybel.examples.vegf_graph import vegf_graph

class TestUtils(unittest.TestCase):
    def test_group_delimited(self):
        self.assertEqual([[5335, 5336], [9047]], group_delimited_list([5335, 5336, '/', 9047], '/'))


class TestImportHipathia(unittest.TestCase):
    """Test Hipathia import."""

    def test_import(self):
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


class TestExportHipathia(unittest.TestCase):
    """Test Hipathia."""

    def test_complex(self):
        """Test that proteins in complex are all required (AND gate)."""
        # HipathiaConverter(sialic_acid_graph)

    def test_family(self):
        """Test that one or more proteins from a family are required (OR gate)."""
        # HipathiaConverter(vegf_graph)

    def test_famplex(self):
        """Test the cartesian product on a family of proteins in a complex are required."""
        # HipathiaConverter(ampk_graph)

    def test_example(self):
        """Test the stuff works for real

        1. Load example graph
        2. Export for hipathia (use temprary directory)
        3. load up correct one
        4. check the nodes are right in the ATT and SIF files (do some preprocesing to fix the names)
        """
        test_graph = make_hsa047370()
        hipathia_object = HipathiaConverter(test_graph)

        d = tempfile.TemporaryDirectory()

        # TODO: replace with d.name
        hipathia_object.output('/Users/danieldomingo/PycharmProjects/pybel/tests')

        d.cleanup()
