import unittest

import networkx as nx

import pybel.utils


class TestUtils(unittest.TestCase):
    def test_expand_dict(self):
        flat_dict = {
            'k1': 'v1',
            'k2_k2a': 'v2',
            'k2_k2b': 'v3',
            'k2_k2c_k2ci': 'v4',
            'k2_k2c_k2cii': 'v5'
        }

        expected_dict = {
            'k1': 'v1',
            'k2': {
                'k2a': 'v2',
                'k2b': 'v3',
                'k2c': {
                    'k2ci': 'v4',
                    'k2cii': 'v5'
                }
            }
        }

        self.assertEqual(expected_dict, pybel.utils.expand_dict(flat_dict))

    def test_flatten_dict(self):
        d = {
            'A': 5,
            'B': 'b',
            'C': {
                'D': 'd',
                'E': 'e'
            }
        }

        expected = {
            'A': 5,
            'B': 'b',
            'C_D': 'd',
            'C_E': 'e'
        }
        self.assertEqual(expected, pybel.utils.flatten(d))

    def test_flatten_dict_withLists(self):
        d = {
            'A': 5,
            'B': 'b',
            'C': {
                'D': ['d', 'delta'],
                'E': 'e'
            }
        }

        expected = {
            'A': 5,
            'B': 'b',
            'C_D': 'd,delta',
            'C_E': 'e'
        }
        self.assertEqual(expected, pybel.utils.flatten(d))

    def test_flatten_edges(self):
        g = nx.MultiDiGraph()
        g.add_edge(1, 2, key=5, attr_dict={'A': 'a', 'B': {'C': 'c', 'D': 'd'}})

        result = pybel.utils.flatten_graph_data(g)

        expected = nx.MultiDiGraph()
        expected.add_edge(1, 2, key=5, attr_dict={'A': 'a', 'B_C': 'c', 'B_D': 'd'})

        self.assertEqual(set(result.nodes()), set(expected.nodes()))

        res_edges = result.edges(keys=True)
        exp_edges = expected.edges(keys=True)
        self.assertEqual(set(res_edges), set(exp_edges))

        for u, v, k in expected.edges(keys=True):
            self.assertEqual(expected[u][v][k], result[u][v][k])
