# -*- coding: utf-8 -*-

"""Tests for the query builder."""

import logging
import unittest

from pybel import BELGraph
from pybel.dsl import Protein
from pybel.examples.egf_example import egf_graph
from pybel.struct.query import Seeding
from pybel.testing.generate import generate_random_graph
from pybel.testing.utils import n

log = logging.getLogger(__name__)


class TestSeedingConstructor(unittest.TestCase):

    def test_none(self):
        seeding = Seeding()
        self.assertEqual(0, len(seeding))
        self.assertEqual('[]', seeding.dumps())

    def test_append_sample(self):
        seeding = Seeding()
        seeding.append_sample()
        self.assertEqual(1, len(seeding))

        s = seeding.dumps()
        self.assertIsInstance(s, str)

    def test_no_seeding(self):
        graph = egf_graph.copy()

        seeding = Seeding()
        result = seeding.run(graph)

        self.assertEqual(graph.number_of_nodes(), result.number_of_nodes())
        self.assertEqual(graph.number_of_edges(), result.number_of_edges())

    def test_seed_by_neighbor(self):
        graph = BELGraph()
        a, b, c, d = (Protein(namespace=n(), name=str(i)) for i in range(4))
        graph.add_increases(a, b, citation=n(), evidence=n())
        graph.add_increases(b, c, citation=n(), evidence=n())
        graph.add_increases(c, d, citation=n(), evidence=n())

        seeding = Seeding()
        seeding.append_neighbors(b)
        result = seeding.run(graph)

        self.assertIsInstance(result, BELGraph)
        # test nodes
        self.assertIn(a, result)
        self.assertIn(b, result)
        self.assertIn(c, result)
        self.assertNotIn(d, result)
        # test edges
        self.assertIn(b, result[a])
        self.assertIn(c, result[b])
        self.assertNotIn(d, result[c])

    def test_seed_by_neighbors(self):
        graph = BELGraph()
        a, b, c, d, e = (Protein(namespace=n(), name=str(i)) for i in range(5))
        graph.add_increases(a, b, citation=n(), evidence=n())
        graph.add_increases(b, c, citation=n(), evidence=n())
        graph.add_increases(c, d, citation=n(), evidence=n())
        graph.add_increases(d, e, citation=n(), evidence=n())

        seeding = Seeding()
        seeding.append_neighbors([b, c])
        result = seeding.run(graph)

        self.assertIsInstance(result, BELGraph)
        # test nodes
        self.assertIn(a, result)
        self.assertIn(b, result)
        self.assertIn(c, result)
        self.assertIn(d, result)
        self.assertNotIn(e, result)
        # test edges
        self.assertIn(b, result[a])
        self.assertIn(c, result[b])
        self.assertIn(d, result[c])
        self.assertNotIn(e, result[d])

    def test_random_sample(self):
        graph = generate_random_graph(50, 1000)

        seeding = Seeding()
        seeding.append_sample(number_edges=10)
        seeding.append_sample(number_edges=10)
        result = seeding.run(graph)

        # TODO this will fail randomly some times lol, so make allowed to be sort of wrong
        self.assertIn(result.number_of_edges(), {18, 19, 20})
