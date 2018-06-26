# -*- coding: utf-8 -*-

import string
import unittest

from pybel import BELGraph
from pybel.constants import ASSOCIATION, DECREASES, FUNCTION, INCREASES, PROTEIN
from pybel.dsl import gene, protein, rna
from pybel.struct.mutation import expand_upstream_causal, get_upstream_causal_subgraph
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

    def test_get_upstream_causal_subgraph(self):
        a, b, c, d, e, f = [protein(namespace='test', name=n()) for _ in range(6)]
        citation, evidence = '', ''

        universe = BELGraph()
        universe.namespace_pattern['test'] = 'test-url'
        universe.add_qualified_edge(a, b, INCREASES, citation, evidence)
        universe.add_qualified_edge(b, c, INCREASES, citation, evidence)
        universe.add_qualified_edge(d, a, ASSOCIATION, citation, evidence)
        universe.add_qualified_edge(e, a, INCREASES, citation, evidence)
        universe.add_qualified_edge(f, b, DECREASES, citation, evidence)

        subgraph = get_upstream_causal_subgraph(universe, [a.as_tuple(), b.as_tuple()])

        self.assertIn('test', subgraph.namespace_pattern)
        self.assertEqual('test-url', subgraph.namespace_pattern['test'])

        self.assertInGraph(a, subgraph)
        self.assertIn(FUNCTION, subgraph.node[a.as_tuple()])
        self.assertEqual(PROTEIN, subgraph.node[a.as_tuple()][FUNCTION])
        self.assertInGraph(b, subgraph)
        self.assertNotInGraph(c, subgraph)
        self.assertNotInGraph(d, subgraph)
        self.assertInGraph(e, subgraph)
        self.assertInGraph(f, subgraph)
        self.assertIn(FUNCTION, subgraph.node[f.as_tuple()])
        self.assertEqual(PROTEIN, subgraph.node[f.as_tuple()][FUNCTION])
        self.assertEqual(4, subgraph.number_of_nodes())

        self.assertInEdge(e, a, subgraph)
        self.assertInEdge(a, b, subgraph)
        self.assertInEdge(f, b, subgraph)
        self.assertEqual(3, subgraph.number_of_edges())

    def test_expand_upstream_causal_subgraph(self):
        a, b, c, d, e, f = [protein(namespace='test', name=i) for i in string.ascii_lowercase[:6]]
        citation, evidence = '', ''

        universe = BELGraph()
        universe.add_qualified_edge(a, b, INCREASES, citation, evidence)
        universe.add_qualified_edge(b, c, INCREASES, citation, evidence)
        universe.add_qualified_edge(d, a, ASSOCIATION, citation, evidence)
        universe.add_qualified_edge(e, a, INCREASES, citation, evidence)
        universe.add_qualified_edge(f, b, DECREASES, citation, evidence)

        subgraph = BELGraph()
        subgraph.add_qualified_edge(a, b, INCREASES, citation, evidence)

        expand_upstream_causal(universe, subgraph)

        self.assertInGraph(a, subgraph)
        self.assertIn(FUNCTION, subgraph.node[a.as_tuple()])
        self.assertEqual(PROTEIN, subgraph.node[a.as_tuple()][FUNCTION])
        self.assertInGraph(b, subgraph)
        self.assertNotInGraph(c, subgraph)
        self.assertNotInGraph(d, subgraph)
        self.assertInGraph(e, subgraph)
        self.assertInGraph(f, subgraph)
        self.assertIn(FUNCTION, subgraph.node[f.as_tuple()])
        self.assertEqual(PROTEIN, subgraph.node[f.as_tuple()][FUNCTION])
        self.assertEqual(4, subgraph.number_of_nodes())

        self.assertInEdge(e, a, subgraph)
        self.assertInEdge(a, b, subgraph)
        self.assertInEdge(f, b, subgraph)
        self.assertEqual(2, len(subgraph[a.as_tuple()][b.as_tuple()]))
        self.assertEqual(4, subgraph.number_of_edges(), msg='\n'.join(map(str, subgraph.edges())))
