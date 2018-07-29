# -*- coding: utf-8 -*-

"""Tests for PyBEL induction functions."""

import string
import unittest

from pybel import BELGraph
from pybel.constants import (
    ASSOCIATION, CITATION_AUTHORS, CITATION_REFERENCE, CITATION_TYPE, CITATION_TYPE_PUBMED,
    DECREASES, FUNCTION, INCREASES, PROTEIN,
)
from pybel.dsl import gene, protein, rna
from pybel.struct.mutation.expansion import expand_upstream_causal
from pybel.struct.mutation.induction.citation import get_subgraph_by_authors, get_subgraph_by_pubmed
from pybel.struct.mutation.induction.paths import get_nodes_in_all_shortest_paths, get_subgraph_by_all_shortest_paths
from pybel.struct.mutation.induction.upstream import get_upstream_causal_subgraph
from pybel.struct.mutation.induction.utils import get_subgraph_by_induction
from pybel.testing.utils import n

trem2_gene = gene(namespace='HGNC', name='TREM2')
trem2_rna = rna(namespace='HGNC', name='TREM2')
trem2_protein = protein(namespace='HGNC', name='TREM2')


class TestGraphMixin(unittest.TestCase):
    """A mixin to enable testing nodes and edge membership in the graph."""

    def assert_in_graph(self, node, graph):
        """Assert the node is in the graph.

        :type node: pybel.dsl.BaseEntity
        :type graph: pybel.BELGraph
        :rtype: bool
        """
        self.assertTrue(graph.has_node_with_data(node))

    def assert_not_in_graph(self, node, graph):
        """Assert the node is not in the graph.

        :type node: pybel.dsl.BaseEntity
        :type graph: pybel.BELGraph
        :rtype: bool
        """
        self.assertFalse(graph.has_node_with_data(node))

    def assert_in_edge(self, source, target, graph):
        """Assert the edge is in the graph.

        :param source:
        :param target:
        :type graph: pybel.BELGraph
        :rtype: bool
        """
        self.assertIn(target.as_tuple(), graph[source.as_tuple()])


class TestInduction(TestGraphMixin):
    """Test induction functions."""

    def test_get_subgraph_by_induction(self):
        """Test get_subgraph_by_induction."""
        graph = BELGraph()
        keyword, url = n(), n()
        graph.namespace_url[keyword] = url
        a, b, c, d = [protein(namespace='test', name=n()) for _ in range(4)]
        graph.add_directly_increases(a, b, n(), n())
        graph.add_directly_increases(b, c, n(), n())
        graph.add_directly_increases(c, d, n(), n())
        graph.add_increases(a, d, n(), n())

        nodes = [b.as_tuple(), c.as_tuple()]
        subgraph = get_subgraph_by_induction(graph, nodes)

        self.assertIn(keyword, subgraph.namespace_url)
        self.assertEqual(url, subgraph.namespace_url[keyword])

        self.assert_not_in_graph(a, subgraph)
        self.assert_in_graph(b, subgraph)
        self.assert_in_graph(c, subgraph)
        self.assert_not_in_graph(d, subgraph)

    def test_get_subgraph_by_all_shortest_paths(self):
        """Test get_subgraph_by_all_shortest_paths."""
        graph = BELGraph()
        keyword, url = n(), n()
        graph.namespace_url[keyword] = url
        a, b, c, d, e, f = [protein(namespace='test', name=n()) for _ in range(6)]
        graph.add_increases(a, b, n(), n())
        graph.add_increases(a, c, n(), n())
        graph.add_increases(b, d, n(), n())
        graph.add_increases(c, d, n(), n())
        graph.add_increases(a, e, n(), n())
        graph.add_increases(e, f, n(), n())
        graph.add_increases(f, d, n(), n())

        query_nodes = [a.as_tuple(), d.as_tuple()]
        shortest_paths_nodes = get_nodes_in_all_shortest_paths(graph, query_nodes)
        self.assertIn(a.as_tuple(), shortest_paths_nodes)
        self.assertIn(b.as_tuple(), shortest_paths_nodes)
        self.assertIn(c.as_tuple(), shortest_paths_nodes)
        self.assertIn(d.as_tuple(), shortest_paths_nodes)

        subgraph = get_subgraph_by_all_shortest_paths(graph, query_nodes)

        self.assertIn(keyword, subgraph.namespace_url)
        self.assertEqual(url, subgraph.namespace_url[keyword])

        self.assert_in_graph(a, subgraph)
        self.assert_in_graph(b, subgraph)
        self.assert_in_graph(c, subgraph)
        self.assert_in_graph(d, subgraph)
        self.assert_not_in_graph(e, subgraph)
        self.assert_not_in_graph(f, subgraph)

    def test_get_upstream_causal_subgraph(self):
        """Test get_upstream_causal_subgraph."""
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

        self.assert_in_graph(a, subgraph)
        self.assertIn(FUNCTION, subgraph.node[a.as_tuple()])
        self.assertEqual(PROTEIN, subgraph.node[a.as_tuple()][FUNCTION])
        self.assert_in_graph(b, subgraph)
        self.assert_not_in_graph(c, subgraph)
        self.assert_not_in_graph(d, subgraph)
        self.assert_in_graph(e, subgraph)
        self.assert_in_graph(f, subgraph)
        self.assertIn(FUNCTION, subgraph.node[f.as_tuple()])
        self.assertEqual(PROTEIN, subgraph.node[f.as_tuple()][FUNCTION])
        self.assertEqual(4, subgraph.number_of_nodes())

        self.assert_in_edge(e, a, subgraph)
        self.assert_in_edge(a, b, subgraph)
        self.assert_in_edge(f, b, subgraph)
        self.assertEqual(3, subgraph.number_of_edges())

    def test_expand_upstream_causal_subgraph(self):
        """Test expanding on the upstream causal subgraph."""
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

        self.assert_in_graph(a, subgraph)
        self.assertIn(FUNCTION, subgraph.node[a.as_tuple()])
        self.assertEqual(PROTEIN, subgraph.node[a.as_tuple()][FUNCTION])
        self.assert_in_graph(b, subgraph)
        self.assert_not_in_graph(c, subgraph)
        self.assert_not_in_graph(d, subgraph)
        self.assert_in_graph(e, subgraph)
        self.assert_in_graph(f, subgraph)
        self.assertIn(FUNCTION, subgraph.node[f.as_tuple()])
        self.assertEqual(PROTEIN, subgraph.node[f.as_tuple()][FUNCTION])
        self.assertEqual(4, subgraph.number_of_nodes())

        self.assert_in_edge(e, a, subgraph)
        self.assert_in_edge(a, b, subgraph)
        self.assert_in_edge(f, b, subgraph)
        self.assertEqual(2, len(subgraph[a.as_tuple()][b.as_tuple()]))
        self.assertEqual(4, subgraph.number_of_edges(), msg='\n'.join(map(str, subgraph.edges())))


class TestEdgePredicateBuilders(TestGraphMixin):
    """Tests for edge predicate builders."""

    def test_build_pmid_inclusion_filter(self):
        """Test getting a sub-graph by a single PubMed identifier."""
        a, b, c, d = [protein(namespace='test', name=n()) for _ in range(4)]
        p1, p2, p3, p4 = n(), n(), n(), n()

        graph = BELGraph()
        keyword, url = n(), n()
        graph.namespace_url[keyword] = url
        graph.add_increases(a, b, n(), citation=p1)
        graph.add_increases(a, b, n(), citation=p2)
        graph.add_increases(b, c, n(), citation=p1)
        graph.add_increases(b, c, n(), citation=p3)
        graph.add_increases(c, d, n(), citation=p3)

        subgraph = get_subgraph_by_pubmed(graph, p1)

        self.assertIn(keyword, subgraph.namespace_url)
        self.assertEqual(url, subgraph.namespace_url[keyword])

        self.assert_in_graph(a, subgraph)
        self.assert_in_graph(b, subgraph)
        self.assert_in_graph(c, subgraph)
        self.assert_not_in_graph(d, subgraph)

        empty_subgraph = get_subgraph_by_pubmed(graph, p4)
        self.assertIn(keyword, subgraph.namespace_url)
        self.assertEqual(url, subgraph.namespace_url[keyword])
        self.assertEqual(0, empty_subgraph.number_of_nodes())

    def test_build_pmid_set_inclusion_filter(self):
        """Test getting a sub-graph by a set of PubMed identifiers."""
        a, b, c, d, e, f = [protein(namespace='test', name=n()) for _ in range(6)]
        p1, p2, p3, p4, p5, p6 = n(), n(), n(), n(), n(), n()

        graph = BELGraph()
        keyword, url = n(), n()
        graph.namespace_url[keyword] = url
        graph.add_increases(a, b, n(), citation=p1)
        graph.add_increases(a, b, n(), citation=p2)
        graph.add_increases(b, c, n(), citation=p1)
        graph.add_increases(b, c, n(), citation=p3)
        graph.add_increases(c, d, n(), citation=p3)
        graph.add_increases(e, f, n(), citation=p4)

        subgraph = get_subgraph_by_pubmed(graph, [p1, p4])

        self.assertIn(keyword, subgraph.namespace_url)
        self.assertEqual(url, subgraph.namespace_url[keyword])

        self.assert_in_graph(a, subgraph)
        self.assert_in_graph(b, subgraph)
        self.assert_in_graph(c, subgraph)
        self.assert_not_in_graph(d, subgraph)
        self.assert_in_graph(e, subgraph)
        self.assert_in_graph(f, subgraph)

        empty_subgraph = get_subgraph_by_pubmed(graph, [p5, p6])
        self.assertIn(keyword, subgraph.namespace_url)
        self.assertEqual(url, subgraph.namespace_url[keyword])
        self.assertEqual(0, empty_subgraph.number_of_nodes())

    def test_build_author_inclusion_filter(self):
        """Test getting a sub-graph by a single author."""
        a, b, c, d = [protein(namespace='test', name=n()) for _ in range(4)]
        a1, a2, a3, a4, a5 = n(), n(), n(), n(), n()

        c1 = {
            CITATION_TYPE: CITATION_TYPE_PUBMED,
            CITATION_REFERENCE: n(),
            CITATION_AUTHORS: [a1, a2, a3]
        }
        c2 = {
            CITATION_TYPE: CITATION_TYPE_PUBMED,
            CITATION_REFERENCE: n(),
            CITATION_AUTHORS: [a1, a4]
        }

        graph = BELGraph()
        keyword, url = n(), n()
        graph.namespace_url[keyword] = url
        graph.add_increases(a, b, n(), citation=c1)
        graph.add_increases(a, b, n(), citation=c2)
        graph.add_increases(b, c, n(), citation=c1)
        graph.add_increases(c, d, n(), citation=c2)

        subgraph1 = get_subgraph_by_authors(graph, a1)

        self.assertIn(keyword, subgraph1.namespace_url)
        self.assertEqual(url, subgraph1.namespace_url[keyword])

        self.assert_in_graph(a, subgraph1)
        self.assert_in_graph(b, subgraph1)
        self.assert_in_graph(c, subgraph1)
        self.assert_in_graph(d, subgraph1)

        subgraph2 = get_subgraph_by_authors(graph, a2)

        self.assertIn(keyword, subgraph2.namespace_url)
        self.assertEqual(url, subgraph2.namespace_url[keyword])

        self.assert_in_graph(a, subgraph2)
        self.assert_in_graph(b, subgraph2)
        self.assert_in_graph(c, subgraph2)
        self.assert_not_in_graph(d, subgraph2)

        subgraph3 = get_subgraph_by_authors(graph, a5)
        self.assertIn(keyword, subgraph3.namespace_url)
        self.assertEqual(url, subgraph3.namespace_url[keyword])
        self.assertEqual(0, subgraph3.number_of_nodes())

    def test_build_author_set_inclusion_filter(self):
        """Test getting a sub-graph by a set of authors."""
        a, b, c, d = [protein(namespace='test', name=n()) for _ in range(4)]
        a1, a2, a3, a4 = n(), n(), n(), n()

        c1 = {
            CITATION_TYPE: CITATION_TYPE_PUBMED,
            CITATION_REFERENCE: n(),
            CITATION_AUTHORS: [a1, a2, a3]
        }
        c2 = {
            CITATION_TYPE: CITATION_TYPE_PUBMED,
            CITATION_REFERENCE: n(),
            CITATION_AUTHORS: [a1, a4]
        }

        graph = BELGraph()
        keyword, url = n(), n()
        graph.namespace_url[keyword] = url
        graph.add_increases(a, b, n(), citation=c1)
        graph.add_increases(a, b, n(), citation=c2)
        graph.add_increases(b, c, n(), citation=c1)
        graph.add_increases(c, d, n(), citation=c2)

        subgraph1 = get_subgraph_by_authors(graph, [a1, a2])

        self.assertIn(keyword, subgraph1.namespace_url)
        self.assertEqual(url, subgraph1.namespace_url[keyword])

        self.assert_in_graph(a, subgraph1)
        self.assert_in_graph(b, subgraph1)
        self.assert_in_graph(c, subgraph1)
        self.assert_in_graph(d, subgraph1)
