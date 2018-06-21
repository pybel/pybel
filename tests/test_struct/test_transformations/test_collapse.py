# -*- coding: utf-8 -*-

import unittest

from pybel import BELGraph
from pybel.constants import *
from pybel.dsl import *
from pybel.struct.mutation.collapse import collapse_by_central_dogma, collapse_nodes
from pybel.testing.utils import n

HGNC = 'HGNC'
GO = 'GO'
CHEBI = 'CHEBI'

g1 = gene(HGNC, '1')
r1 = rna(HGNC, '1')
p1 = protein(HGNC, '1')

g2 = gene(HGNC, '2')
r2 = rna(HGNC, '2')
p2 = protein(HGNC, '2')

g3 = gene(HGNC, '3')
r3 = rna(HGNC, '3')
p3 = protein(HGNC, '3')

g4 = gene(HGNC, '4')
m4 = mirna(HGNC, '4')

a5 = abundance(CHEBI, '5')
p5 = pathology(GO, '5')


class TestCollapseDownstream(unittest.TestCase):
    def test_collapse_1(self):
        graph = BELGraph()
        graph.add_node_from_data(p1)
        graph.add_node_from_data(p2)
        graph.add_node_from_data(p3)

        graph.add_increases(p1, p3, citation=n(), evidence=n())
        graph.add_qualified_edge(p2, p3, relation=DIRECTLY_INCREASES, citation=n(), evidence=n())

        self.assertEqual(3, graph.number_of_nodes())
        self.assertEqual(2, graph.number_of_edges())

        d = {
            p1.as_tuple(): {p2.as_tuple()}
        }

        collapse_nodes(graph, d)

        self.assertEqual({p1.as_tuple(), p3.as_tuple()}, set(graph))
        self.assertEqual({(p1.as_tuple(), p3.as_tuple()), (p1.as_tuple(), p3.as_tuple())}, set(graph.edges()))
        self.assertEqual(1, graph.number_of_edges(), msg=graph.edges(data=True, keys=True))

    def test_collapse_dogma_1(self):
        graph = BELGraph()
        graph.add_translation(r1, p1)

        self.assertEqual(2, graph.number_of_nodes())
        self.assertEqual(1, graph.number_of_edges())

        collapse_by_central_dogma(graph)

        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())

    def test_collapse_dogma_2(self):
        graph = BELGraph()
        graph.add_transcription(g1, r1)
        graph.add_translation(r1, p1)

        self.assertEqual(3, graph.number_of_nodes())
        self.assertEqual(2, graph.number_of_edges())

        collapse_by_central_dogma(graph)

        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())

    def test_collapse_dogma_3(self):
        graph = BELGraph()
        graph.add_transcription(g1, r1)

        self.assertEqual(2, graph.number_of_nodes())
        self.assertEqual(1, graph.number_of_edges())

        collapse_by_central_dogma(graph)

        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())
