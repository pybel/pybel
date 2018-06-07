# -*- coding: utf-8 -*-

import unittest

from pybel import BELGraph
from pybel.constants import ASSOCIATION, DECREASES, INCREASES
from pybel.dsl import gene, protein, rna
from pybel.struct.mutation import expand_upstream_causal_subgraph

trem2_gene = gene(namespace='HGNC', name='TREM2')
trem2_rna = rna(namespace='HGNC', name='TREM2')
trem2_protein = protein(namespace='HGNC', name='TREM2')


class TestInduction(unittest.TestCase):

    def test_expand_upstream_causal_subgraph(self):
        a, b, c, d, e, f = [protein(namespace='test', name=str(i)) for i in range(6)]
        citation, evidence = '', ''

        universe = BELGraph()
        universe.add_qualified_edge(a, b, INCREASES, citation, evidence)
        universe.add_qualified_edge(b, c, INCREASES, citation, evidence)
        universe.add_qualified_edge(d, a, ASSOCIATION, citation, evidence)
        universe.add_qualified_edge(e, a, INCREASES, citation, evidence)
        universe.add_qualified_edge(f, b, DECREASES, citation, evidence)

        subgraph = BELGraph()
        subgraph.add_qualified_edge(a, b, INCREASES, citation, evidence)

        expand_upstream_causal_subgraph(universe, subgraph)

        self.assertIn(a, subgraph)
        self.assertIn(b, subgraph)
        self.assertNotIn(c, subgraph)
        self.assertNotIn(d, subgraph)
        self.assertIn(e, subgraph)
        self.assertIn(f, subgraph)
        self.assertEqual(4, subgraph.number_of_nodes())

        self.assertIn(a, subgraph[e])
        self.assertIn(b, subgraph[a])
        self.assertIn(b, subgraph[f])
        self.assertEqual(3, subgraph.number_of_edges())
