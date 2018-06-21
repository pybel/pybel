# -*- coding: utf-8 -*-

import unittest

from pybel import BELGraph
from pybel.constants import INCREASES
from pybel.dsl import protein
from pybel.dsl.nodes import BaseEntity
from pybel.struct.grouping import get_subgraphs_by_annotation
from pybel.testing.utils import n


class TestGrouping(unittest.TestCase):

    def assertIn(self, x, c):
        if not isinstance(c, BELGraph):
            return unittest.TestCase.assertIn(self, x, c)
        if isinstance(x, BaseEntity):
            return unittest.TestCase.assertIn(self, x.as_tuple(), c)
        if isinstance(x, tuple):
            return unittest.TestCase.assertIn(self, x, c)
        raise TypeError

    def test_get_subgraphs_by_annotation(self):
        graph = BELGraph()
        test_namespace_url = n()
        test_annotation_url = n()
        graph.namespace_url['test'] = test_namespace_url
        graph.annotation_url['subgraph'] = test_annotation_url

        a, b, c, d = [protein(namespace='test', name=str(i)) for i in range(4)]
        citation, evidence = n(), n()

        graph.add_qualified_edge(a, b, INCREASES, citation, evidence, annotations={'subgraph': {'1', '2'}})
        graph.add_qualified_edge(a, c, INCREASES, citation, evidence, annotations={'subgraph': {'1'}})
        graph.add_qualified_edge(b, d, INCREASES, citation, evidence, annotations={'subgraph': {'1', '2'}})
        graph.add_qualified_edge(a, d, INCREASES, citation, evidence, annotations={'subgraph': {'2'}})
        graph.add_qualified_edge(c, d, INCREASES, citation, evidence)

        subgraphs = get_subgraphs_by_annotation(graph, annotation='subgraph', keep_undefined=False)

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

        self.assertIn(b.as_tuple(), subgraph_1[a.as_tuple()])
        self.assertIn(c.as_tuple(), subgraph_1[a.as_tuple()])
        self.assertIn(d.as_tuple(), subgraph_1[b.as_tuple()])
        self.assertNotIn(d.as_tuple(), subgraph_1[a.as_tuple()])
        self.assertNotIn(d.as_tuple(), subgraph_1[c.as_tuple()])

        subgraph_2 = subgraphs['2']
        self.assertIsInstance(subgraph_2, BELGraph)

        self.assertIn('test', subgraph_2.namespace_url)
        self.assertIn('subgraph', subgraph_2.annotation_url)

        self.assertIn(a, subgraph_2)
        self.assertIn(b, subgraph_2)
        self.assertNotIn(c, subgraph_2)
        self.assertIn(d, subgraph_2)

        self.assertIn(b.as_tuple(), subgraph_2[a.as_tuple()])
        self.assertNotIn(c.as_tuple(), subgraph_2[a.as_tuple()])
        self.assertIn(d.as_tuple(), subgraph_2[b.as_tuple()])
        self.assertIn(d.as_tuple(), subgraph_2[a.as_tuple()])
