# -*- coding: utf-8 -*-

import unittest

from pybel import BELGraph
from pybel.constants import GRAPH_METADATA, METADATA_NAME, METADATA_VERSION


class TestStruct(unittest.TestCase):
    def test_add_simple(self):
        g = BELGraph()

        g.add_simple_node('A', 'B', 'C')
        self.assertEqual(1, g.number_of_nodes())

        g.add_simple_node('A', 'B', 'C')
        self.assertEqual(1, g.number_of_nodes())

    def test_str(self):
        g = BELGraph(**{GRAPH_METADATA: {METADATA_NAME: 'test', METADATA_VERSION: '1.0.0'}})
        self.assertEqual('test v1.0.0', str(g))

    def test_name(self):
        g = BELGraph(**{GRAPH_METADATA: {METADATA_NAME: 'test'}})
        self.assertEqual('test', g.name)

        g.name = 'other test'
        self.assertEqual('other test', g.name)


if __name__ == '__main__':
    unittest.main()
