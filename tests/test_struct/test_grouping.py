# -*- coding: utf-8 -*-

import unittest

from pybel import BELGraph
from pybel.constants import FUNCTION, PROTEIN
from pybel.dsl import protein
from pybel.dsl.nodes import BaseEntity
from pybel.struct.grouping import get_subgraphs_by_annotation
from pybel.testing.utils import n

test_namespace_url = n()
test_annotation_url = n()
citation, evidence = n(), n()
a, b, c, d = [protein(namespace='test', name=str(i)) for i in range(4)]


class TestGrouping(unittest.TestCase):

    def assertIn(self, x, c):
        if not isinstance(c, BELGraph):
            return unittest.TestCase.assertIn(self, x, c)
        if isinstance(x, BaseEntity):
            return unittest.TestCase.assertIn(self, x.as_tuple(), c)
        if isinstance(x, tuple):
            return unittest.TestCase.assertIn(self, x, c)
        raise TypeError

    def setUp(self):
        self.graph = BELGraph()

        self.graph.namespace_url['test'] = test_namespace_url
        self.graph.annotation_url['subgraph'] = test_annotation_url

        self.graph.add_increases(a, b, citation=citation, evidence=evidence, annotations={'subgraph': {'1', '2'}})
        self.graph.add_increases(a, c, citation=citation, evidence=evidence,  annotations={'subgraph': {'1'}})
        self.graph.add_increases(b, d, citation=citation, evidence=evidence,  annotations={'subgraph': {'1', '2'}})
        self.graph.add_increases(a, d, citation=citation, evidence=evidence,  annotations={'subgraph': {'2'}})
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
        self.assertIn(FUNCTION, subgraph_1.node[a.as_tuple()])
        self.assertEqual(PROTEIN, subgraph_1.node[a.as_tuple()][FUNCTION])
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

    def test_get_subgraphs_by_annotation_with_sentinel(self):
        sentinel = n()
        subgraphs = get_subgraphs_by_annotation(self.graph, annotation='subgraph', sentinel=sentinel)

        self.assertEqual(3, len(subgraphs))
        self.assertIn('1', subgraphs)
        self.assertIn('2', subgraphs)
        self.assertIn(sentinel, subgraphs)
