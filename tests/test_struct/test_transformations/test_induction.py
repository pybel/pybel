# -*- coding: utf-8 -*-

import unittest

from pybel import BELGraph
from pybel.constants import ASSOCIATION, DECREASES, INCREASES
from pybel.dsl import gene, protein, rna
from pybel.struct.mutation import expand_upstream_causal_subgraph
from pybel.testing.utils import n

trem2_gene = gene(namespace='HGNC', name='TREM2')
trem2_rna = rna(namespace='HGNC', name='TREM2')
trem2_protein = protein(namespace='HGNC', name='TREM2')


class TestInduction(unittest.TestCase):
    def assertInGraph(self, node, graph):
        """Assert the node is in the graph.

        :type node: pybel.dsl.BaseEntity
        :type graph: pybel.BELGraph
        :rtype: bool
        """
        self.assertTrue(graph.has_node_with_data(node))

    def assertNotInGraph(self, node, graph):
        """Assert the node is not in the graph.

        :type node: pybel.dsl.BaseEntity
        :type graph: pybel.BELGraph
        :rtype: bool
        """
        self.assertFalse(graph.has_node_with_data(node))

    def assertInEdge(self, source, target, graph):
        """

        :param source:
        :param target:
        :param graph:
        :return:
        """
        self.assertIn(target.as_tuple(), graph[source.as_tuple()])

    def test_expand_upstream_causal_subgraph(self):
        a, b, c, d, e, f = (protein(namespace='test', name=n()) for _ in range(6))
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

        self.assertInGraph(a, subgraph)
        self.assertInGraph(b, subgraph)
        self.assertNotInGraph(c, subgraph)
        self.assertNotInGraph(d, subgraph)
        self.assertInGraph(e, subgraph)
        self.assertInGraph(f, subgraph)
        self.assertEqual(4, subgraph.number_of_nodes())

        self.assertInEdge(e, a, subgraph)
        self.assertInEdge(a, b, subgraph)
        self.assertInEdge(f, b, subgraph)
        self.assertEqual(3, subgraph.number_of_edges())

