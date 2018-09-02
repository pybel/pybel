# -*- coding: utf-8 -*-

"""Tests for functions for grouping BEL graphs into sub-graphs."""

import unittest

from pybel import BELGraph
from pybel.constants import CITATION_TYPE_PUBMED, FUNCTION, PROTEIN
from pybel.dsl import protein
from pybel.struct.grouping import get_subgraphs_by_annotation, get_subgraphs_by_citation
from pybel.testing.utils import n

test_namespace_url = n()
test_annotation_url = n()
citation, evidence = n(), n()
a, b, c, d = [protein(namespace='test', name=str(i)) for i in range(4)]


class TestAnnotation(unittest.TestCase):
    """Tests for getting sub-graphs by annotation."""

    def setUp(self):
        """Set up the test case with a pre-populated BEL graph."""
        self.graph = BELGraph()

        self.graph.namespace_url['test'] = test_namespace_url
        self.graph.annotation_url['subgraph'] = test_annotation_url

        self.graph.add_increases(a, b, citation=citation, evidence=evidence, annotations={'subgraph': {'1', '2'}})
        self.graph.add_increases(a, c, citation=citation, evidence=evidence, annotations={'subgraph': {'1'}})
        self.graph.add_increases(b, d, citation=citation, evidence=evidence, annotations={'subgraph': {'1', '2'}})
        self.graph.add_increases(a, d, citation=citation, evidence=evidence, annotations={'subgraph': {'2'}})
        self.graph.add_increases(c, d, citation=citation, evidence=evidence)

    def test_get_subgraphs_by_annotation(self):
        subgraphs = get_subgraphs_by_annotation(self.graph, annotation='subgraph')

        self.assertEqual(2, len(subgraphs))
        self.assertIn('1', subgraphs)
        self.assertIn('2', subgraphs)

        subgraph_1 = subgraphs['1']
        self.assertIsInstance(subgraph_1, BELGraph)

        self.assertIn('test', subgraph_1.namespace_url)
        self.assertIn('subgraph', subgraph_1.annotation_url)

        self.assertIn(a, subgraph_1)
        self.assertIn(b, subgraph_1)
        self.assertIn(c, subgraph_1)
        self.assertIn(d, subgraph_1)

        self.assertIn(b, subgraph_1[a])
        self.assertIn(c, subgraph_1[a])
        self.assertIn(d, subgraph_1[b])
        self.assertNotIn(d, subgraph_1[a])
        self.assertNotIn(d, subgraph_1[c])

        subgraph_2 = subgraphs['2']
        self.assertIsInstance(subgraph_2, BELGraph)

        self.assertIn('test', subgraph_2.namespace_url)
        self.assertIn('subgraph', subgraph_2.annotation_url)

        self.assertIn(a, subgraph_2)
        self.assertIn(b, subgraph_2)
        self.assertNotIn(c, subgraph_2)
        self.assertIn(d, subgraph_2)

        self.assertIn(b, subgraph_2[a])
        self.assertNotIn(c, subgraph_2[a])
        self.assertIn(d, subgraph_2[b])
        self.assertIn(d, subgraph_2[a])

    def test_get_subgraphs_by_annotation_with_sentinel(self):
        sentinel = n()
        subgraphs = get_subgraphs_by_annotation(self.graph, annotation='subgraph', sentinel=sentinel)

        self.assertEqual(3, len(subgraphs))
        self.assertIn('1', subgraphs)
        self.assertIn('2', subgraphs)
        self.assertIn(sentinel, subgraphs)


class TestProvenance(unittest.TestCase):
    """Tests for getting sub-graphs by provenance information (citation, etc.)"""

    def test_get_subgraphs_by_citation(self):
        """Test getting sub-graphs by citation."""
        graph = BELGraph()

        c1, c2, c3 = n(), n(), n()

        graph.add_increases(a, b, citation=c1, evidence=n())
        graph.add_increases(a, b, citation=c2, evidence=n())
        graph.add_increases(b, c, citation=c1, evidence=n())
        graph.add_increases(c, d, citation=c1, evidence=n())
        graph.add_increases(a, d, citation=c3, evidence=n())

        subgraphs = get_subgraphs_by_citation(graph)

        # TODO tests for metadata

        c1_pair = (CITATION_TYPE_PUBMED, c1)
        self.assertIn(c1_pair, subgraphs)
        c1_subgraph = subgraphs[c1_pair]
        self.assertIn(a, c1_subgraph)
        self.assertIn(b, c1_subgraph)
        self.assertIn(c, c1_subgraph)
        self.assertIn(d, c1_subgraph)

        c2_pair = (CITATION_TYPE_PUBMED, c2)
        self.assertIn(c2_pair, subgraphs)
        c2_subgraph = subgraphs[c2_pair]
        self.assertIn(a, c2_subgraph)
        self.assertIn(b, c2_subgraph)
        self.assertNotIn(c, c2_subgraph)
        self.assertNotIn(d, c2_subgraph)

        c3_pair = (CITATION_TYPE_PUBMED, c3)
        self.assertIn(c3_pair, subgraphs)
        c3_subgraph = subgraphs[c3_pair]
        self.assertIn(a, c3_subgraph)
        self.assertNotIn(b, c3_subgraph)
        self.assertNotIn(c, c3_subgraph)
        self.assertIn(d, c3_subgraph)
