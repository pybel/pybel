# -*- coding: utf-8 -*-

import unittest

from pybel import BELGraph
from pybel.constants import (
    FUNCTION, GRAPH_METADATA, IDENTIFIER, METADATA_NAME, METADATA_VERSION, NAME, NAMESPACE,
    PROTEIN,
)
from pybel.dsl import *
from pybel.dsl.utils import entity


class TestStruct(unittest.TestCase):
    def test_add_simple(self):
        g = BELGraph()

        g.add_simple_node('A', 'B', 'C')
        self.assertEqual(1, g.number_of_nodes())

        g.add_simple_node('A', 'B', 'C')
        self.assertEqual(1, g.number_of_nodes())

    def test_str(self):
        g = BELGraph(**{GRAPH_METADATA: {METADATA_NAME: 'test', METADATA_VERSION: '1.0.0'}})

        self.assertEqual('test', g.name)
        self.assertEqual('1.0.0', g.version)

        self.assertEqual('test v1.0.0', str(g))

    def test_str_kwargs(self):
        g = BELGraph(name='test', version='1.0.0', description='test description')

        self.assertEqual('test', g.name)
        self.assertEqual('1.0.0', g.version)
        self.assertEqual('test description', g.description)

        self.assertEqual('test v1.0.0', str(g))

    def test_name(self):
        g = BELGraph()

        g.name = 'test'
        g.version = '1.0.0'
        g.description = 'test description'

        self.assertEqual('test', g.name)
        self.assertEqual('1.0.0', g.version)
        self.assertEqual('test description', g.description)

        self.assertEqual('test v1.0.0', str(g))


class TestDSL(unittest.TestCase):
    def test_add_robust_node(self):
        g = BELGraph()

        p = protein(name='yfg', namespace='test', identifier='1')

        p_tuple = g.add_node_from_data(p)

        self.assertEqual(
            {
                FUNCTION: PROTEIN,
                NAMESPACE: 'test',
                NAME: 'yfg',
                IDENTIFIER: '1'
            },
            g.node[p_tuple]
        )

    def test_add_identified_node(self):
        """What happens when a node with only an identifier is added to a graph"""
        g = BELGraph()

        p = protein(namespace='test', identifier='1')

        self.assertNotIn(NAME, p)

        p_tuple = g.add_node_from_data(p)

        self.assertEqual(
            {
                FUNCTION: PROTEIN,
                NAMESPACE: 'test',
                IDENTIFIER: '1'
            },
            g.node[p_tuple]
        )

    def test_missing_information(self):
        """Checks that entity and abundance functions raise on missing name/identifier"""
        with self.assertRaises(ValueError):
            entity(namespace='test')

        with self.assertRaises(ValueError):
            protein(namespace='test')


if __name__ == '__main__':
    unittest.main()
