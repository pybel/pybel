# -*- coding: utf-8 -*-

"""Tests for Hipathia."""

import os
import unittest

from pybel.dsl import ComplexAbundance, Protein
from pybel.io.hipathia import from_hipathia_paths, group_delimited_list

HERE = os.path.abspath(os.path.dirname(__file__))

TEST_1_ATT_PATH = os.path.join(HERE, 'test_1.att')
TEST_1_SIF_PATH = os.path.join(HERE, 'test_1.sif')

TEST_ATT_PATH = os.path.join(HERE, 'hsa04370.att')
TEST_SIF_PATH = os.path.join(HERE, 'hsa04370.sif')


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


class TestUtils(unittest.TestCase):
    def test_group_delimited(self):
        self.assertEqual([[5335, 5336], [9047]], group_delimited_list([5335, 5336, '/', 9047], '/'))
