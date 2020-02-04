# -*- coding: utf-8 -*-

"""Tests for Hipathia."""

import tempfile
import unittest

from pybel import BELGraph
from pybel.dsl import complex_abundance
from pybel.dsl import hgnc
# from pybel.examples.ampk_example import ampk_graph
# from pybel.examples.sialic_acid_example import sialic_acid_graph
# from pybel.examples.vegf_graph import vegf_graph
from pybel.io.hipathia import HipathiaConverter


def make_hsa047370() -> BELGraph:
    """"""
    graph = BELGraph(name='hsa04370')

    node_1 = hgnc('CDC42')
    node_9 = hgnc('KDR')
    node_11 = hgnc('SPHK2')
    node_17 = hgnc('MAPKAPK3')
    node_18 = hgnc('PPP3CA')
    node_19 = hgnc('AKT3')
    node_20 = hgnc('PIK3R5')
    node_21 = hgnc('NFATC2')
    node_22 = hgnc('PRKCA')
    node_24 = hgnc('MAPK14')
    node_27 = hgnc('SRC')
    node_29 = hgnc('VEGFA')
    node_32 = hgnc('MAPK1')
    node_33 = hgnc('MAP2K1')
    node_34 = hgnc('RAF1')
    node_35 = hgnc('HRAS')

    node_10 = complex_abundance([hgnc('PLCG1'), hgnc('SH2D2A')])

    node_28 = hgnc('SHC2')
    node_23 = hgnc('PTK2')
    node_25 = hgnc('PXN')
    node_16 = hgnc('HSPB1')
    node_36 = hgnc('NOS3')
    node_37 = hgnc('CASP9')
    node_38 = hgnc('BAD')
    node_39 = hgnc('RAC1')
    node_14 = hgnc('PTGS2')
    node_15 = hgnc('PLA2G4B')

    def _add_increases(a, b):
        graph.add_directly_increases(a, b, citation='', evidence='')

    def _add_decreases(a, b):
        graph.add_directly_decreases(a, b, citation='', evidence='')

    _add_increases(node_1, node_24)
    _add_increases(node_9, node_28)

    _add_increases(node_9, node_23)
    _add_increases(node_9, node_25)
    _add_increases(node_9, node_20)
    _add_increases(node_9, node_27)
    _add_increases(node_9, node_10)

    _add_increases(node_11, node_35)
    _add_increases(node_17, node_16)
    _add_increases(node_18, node_21)
    _add_increases(node_19, node_36)
    _add_decreases(node_19, node_37)
    _add_decreases(node_19, node_38)
    _add_increases(node_20, node_39)
    _add_increases(node_20, node_19)
    _add_increases(node_21, node_14)
    _add_increases(node_22, node_34)
    _add_increases(node_22, node_11)
    _add_increases(node_24, node_17)
    _add_increases(node_27, node_20)
    _add_increases(node_29, node_9)
    _add_increases(node_32, node_15)
    _add_increases(node_33, node_32)
    _add_increases(node_34, node_33)
    _add_increases(node_35, node_34)
    _add_increases(node_10, node_18)
    _add_increases(node_10, node_22)
    _add_increases(node_10, node_15)
    _add_increases(node_10, node_36)

    return graph


class TestHipathia(unittest.TestCase):
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
