# -*- coding: utf-8 -*-

"""Tests for PyBEL induction functions."""

import string
import unittest

from pybel import BELGraph
from pybel.constants import (
    ASSOCIATION, CITATION_AUTHORS, CITATION_REFERENCE, CITATION_TYPE, CITATION_TYPE_PUBMED,
    DECREASES, FUNCTION, INCREASES, PROTEIN,
)
from pybel.dsl import BaseEntity, gene, protein, rna
from pybel.struct.mutation.expansion import expand_upstream_causal
from pybel.struct.mutation.induction import get_subgraph_by_annotation_value
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

    def assert_in_edge(self, source, target, graph):
        """Assert the edge is in the graph.

        :param source:
        :param target:
        :type graph: pybel.BELGraph
        :rtype: bool
        """
        self.assertIn(target, graph[source])

    def assert_all_nodes_are_base_entities(self, graph):
        """Assert that all nodes are base entities."""
        for node in graph:
            self.assertIsInstance(node, BaseEntity)


class TestInduction(TestGraphMixin):
    """Test induction functions."""

    def test_get_subgraph_by_induction(self):
        """Test get_subgraph_by_induction."""
        graph = BELGraph()
        keyword, url = n(), n()
        graph.namespace_url[keyword] = url
        a, b, c, d = [protein(namespace='test', name=str(i)) for i in range(4)]
        graph.add_directly_increases(a, b, n(), n())
        graph.add_directly_increases(b, c, n(), n())
        graph.add_directly_increases(c, d, n(), n())
        graph.add_increases(a, d, n(), n())

        nodes = [b, c]
        subgraph = get_subgraph_by_induction(graph, nodes)

        self.assertIsInstance(subgraph, BELGraph)
        self.assert_all_nodes_are_base_entities(subgraph)
        self.assertNotEqual(0, len(subgraph.namespace_url), msg='improperly found metadata: {}'.format(subgraph.graph))
        self.assertIn(keyword, subgraph.namespace_url)
        self.assertEqual(url, subgraph.namespace_url[keyword])

        self.assertNotIn(a, subgraph)
        self.assertIn(b, subgraph)
        self.assertIn(c, subgraph)
        self.assertNotIn(d, subgraph)

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

        query_nodes = [a, d]
        shortest_paths_nodes = get_nodes_in_all_shortest_paths(graph, query_nodes)

        self.assertIn(a, shortest_paths_nodes)
        self.assertIn(b, shortest_paths_nodes)
        self.assertIn(c, shortest_paths_nodes)
        self.assertIn(d, shortest_paths_nodes)

        subgraph = get_subgraph_by_all_shortest_paths(graph, query_nodes)
        self.assert_all_nodes_are_base_entities(subgraph)
        self.assertIsInstance(subgraph, BELGraph)
        self.assertIn(keyword, subgraph.namespace_url)
        self.assertEqual(url, subgraph.namespace_url[keyword])

        self.assertIn(a, subgraph)
        self.assertIn(b, subgraph)
        self.assertIn(c, subgraph)
        self.assertIn(d, subgraph)
        self.assertNotIn(e, subgraph)
        self.assertNotIn(f, subgraph)

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

        subgraph = get_upstream_causal_subgraph(universe, [a, b])

        self.assertIsInstance(subgraph, BELGraph)
        self.assert_all_nodes_are_base_entities(subgraph)

        self.assertIn('test', subgraph.namespace_pattern)
        self.assertEqual('test-url', subgraph.namespace_pattern['test'])

        self.assertIn(a, subgraph)
        self.assertIn(b, subgraph)
        self.assertNotIn(c, subgraph)
        self.assertNotIn(d, subgraph)
        self.assertIn(e, subgraph)
        self.assertIn(f, subgraph)
        self.assertEqual(4, subgraph.number_of_nodes())

        self.assert_in_edge(e, a, subgraph)
        self.assert_in_edge(a, b, subgraph)
        self.assert_in_edge(f, b, subgraph)
        self.assertEqual(3, subgraph.number_of_edges())

    def test_expand_upstream_causal_subgraph(self):
        """Test expanding on the upstream causal subgraph."""
        a, b, c, d, e, f = [protein(namespace='test', name=i) for i in string.ascii_lowercase[:6]]

        universe = BELGraph()
        universe.add_qualified_edge(a, b, INCREASES, n(), n())
        universe.add_qualified_edge(b, c, INCREASES, n(), n())
        universe.add_qualified_edge(d, a, ASSOCIATION, n(), n())
        universe.add_qualified_edge(e, a, INCREASES, n(), n())
        universe.add_qualified_edge(f, b, DECREASES, n(), n())

        subgraph = BELGraph()
        subgraph.add_qualified_edge(a, b, INCREASES, n(), n())

        expand_upstream_causal(universe, subgraph)

        self.assertIsInstance(subgraph, BELGraph)
        self.assert_all_nodes_are_base_entities(subgraph)

        self.assertIn(a, subgraph)
        self.assertIn(b, subgraph)
        self.assertNotIn(c, subgraph)
        self.assertNotIn(d, subgraph)
        self.assertIn(e, subgraph)
        self.assertIn(f, subgraph)
        self.assertEqual(4, subgraph.number_of_nodes())

        self.assert_in_edge(e, a, subgraph)
        self.assert_in_edge(a, b, subgraph)
        self.assert_in_edge(f, b, subgraph)
        self.assertEqual(2, len(subgraph[a][b]))
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

        self.assertIsInstance(subgraph, BELGraph)
        self.assert_all_nodes_are_base_entities(subgraph)

        self.assertIn(keyword, subgraph.namespace_url)
        self.assertEqual(url, subgraph.namespace_url[keyword])

        self.assertIn(a, subgraph)
        self.assertIn(b, subgraph)
        self.assertIn(c, subgraph)
        self.assertNotIn(d, subgraph)

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

        self.assertIsInstance(subgraph, BELGraph)
        self.assert_all_nodes_are_base_entities(subgraph)

        self.assertIn(keyword, subgraph.namespace_url)
        self.assertEqual(url, subgraph.namespace_url[keyword])

        self.assertIn(a, subgraph)
        self.assertIn(b, subgraph)
        self.assertIn(c, subgraph)
        self.assertNotIn(d, subgraph)
        self.assertIn(e, subgraph)
        self.assertIn(f, subgraph)

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

        self.assertIsInstance(subgraph1, BELGraph)
        self.assert_all_nodes_are_base_entities(subgraph1)

        self.assertIn(keyword, subgraph1.namespace_url)
        self.assertEqual(url, subgraph1.namespace_url[keyword])

        self.assertIn(a, subgraph1)
        self.assertIn(b, subgraph1)
        self.assertIn(c, subgraph1)
        self.assertIn(d, subgraph1)

        subgraph2 = get_subgraph_by_authors(graph, a2)

        self.assertIsInstance(subgraph2, BELGraph)
        self.assert_all_nodes_are_base_entities(subgraph2)

        self.assertIn(keyword, subgraph2.namespace_url)
        self.assertEqual(url, subgraph2.namespace_url[keyword])

        self.assertIn(a, subgraph2)
        self.assertIn(b, subgraph2)
        self.assertIn(c, subgraph2)
        self.assertNotIn(d, subgraph2)

        subgraph3 = get_subgraph_by_authors(graph, a5)

        self.assertIsInstance(subgraph3, BELGraph)
        self.assert_all_nodes_are_base_entities(subgraph3)

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

        self.assertIsInstance(subgraph1, BELGraph)
        self.assert_all_nodes_are_base_entities(subgraph1)

        self.assertIn(keyword, subgraph1.namespace_url)
        self.assertEqual(url, subgraph1.namespace_url[keyword])

        self.assertIn(a, subgraph1)
        self.assertIn(b, subgraph1)
        self.assertIn(c, subgraph1)
        self.assertIn(d, subgraph1)


class TestEdgeInduction(unittest.TestCase):
    """Test induction over edges."""

    def test_get_subgraph_by_annotation_value(self):
        """Test getting a subgraph by a single annotation value."""
        graph = BELGraph()
        a, b, c, d = [protein(namespace='test', name=n()) for _ in range(4)]

        k1 = graph.add_increases(a, b, citation=n(), evidence=n(), annotations={
            'Subgraph': {'A'}
        })

        k2 = graph.add_increases(a, b, citation=n(), evidence=n(), annotations={
            'Subgraph': {'B'}
        })

        k3 = graph.add_increases(a, b, citation=n(), evidence=n(), annotations={
            'Subgraph': {'A', 'C', 'D'}
        })

        subgraph = get_subgraph_by_annotation_value(graph, 'Subgraph', 'A')
        self.assertIsInstance(subgraph, BELGraph)

        self.assertIn(a, subgraph)
        self.assertIn(b, subgraph)
        self.assertIn(b, subgraph[a])
        self.assertIn(k1, subgraph[a][b])
        self.assertNotIn(k2, subgraph[a][b])
        self.assertIn(k3, subgraph[a][b])

    def test_get_subgraph_by_annotation_values(self):
        """Test getting a subgraph by multiple annotation value."""
        graph = BELGraph()
        a, b, c, d = [protein(namespace='test', name=n()) for _ in range(4)]

        k1 = graph.add_increases(a, b, citation=n(), evidence=n(), annotations={
            'Subgraph': {'A'}
        })

        k2 = graph.add_increases(a, b, citation=n(), evidence=n(), annotations={
            'Subgraph': {'B'}
        })

        k3 = graph.add_increases(a, b, citation=n(), evidence=n(), annotations={
            'Subgraph': {'A', 'C', 'D'}
        })

        k4 = graph.add_increases(a, b, citation=n(), evidence=n(), annotations={
            'Subgraph': {'C', 'D'}
        })

        subgraph = get_subgraph_by_annotation_value(graph, 'Subgraph', {'A', 'C'})
        self.assertIsInstance(subgraph, BELGraph)

        self.assertIn(a, subgraph)
        self.assertIn(b, subgraph)
        self.assertIn(b, subgraph[a])
        self.assertIn(k1, subgraph[a][b])
        self.assertNotIn(k2, subgraph[a][b])
        self.assertIn(k3, subgraph[a][b])
        self.assertIn(k4, subgraph[a][b])
