import unittest

import networkx as nx

from pybel.parser import utils
from pybel.parser.utils import subdict_matches, check_stability


class TestUtils(unittest.TestCase):
    def test_list2tuple(self):
        l = [None, 1, 's', [1, 2, [4], [[]]]]
        e = (None, 1, 's', (1, 2, (4,), ((),)))
        t = utils.list2tuple(l)

        self.assertEqual(t, e)

    def test_subiterator(self):
        d = [
            (True, 0),
            (False, 1),
            (False, 2),
            (True, 1),
            (False, 1),
            (True, 2),
            (False, 1),
            (False, 2),
            (False, 3)
        ]

        it = iter(utils.subitergroup(d, lambda x: x[0]))

        matched, subit = next(it)
        subit = iter(subit)
        self.assertEqual(matched, (True, 0))
        self.assertEqual((False, 1), next(subit))
        self.assertEqual((False, 2), next(subit))

        matched, subit = next(it)
        subit = iter(subit)
        self.assertEqual(matched, (True, 1))
        self.assertEqual((False, 1), next(subit))

        matched, subit = next(it)
        subit = iter(subit)
        self.assertEqual(matched, (True, 2))
        self.assertEqual((False, 1), next(subit))
        self.assertEqual((False, 2), next(subit))
        self.assertEqual((False, 3), next(subit))

    def test_dict_matches_1(self):
        a = {
            'k1': 'v1',
            'k2': 'v2'
        }
        b = {
            'k1': 'v1',
            'k2': 'v2'
        }
        self.assertTrue(subdict_matches(a, b))

    def test_dict_matches_2(self):
        a = {
            'k1': 'v1',
            'k2': 'v2',
            'k3': 'v3'
        }
        b = {
            'k1': 'v1',
            'k2': 'v2'
        }
        self.assertTrue(subdict_matches(a, b))

    def test_dict_matches_3(self):
        a = {
            'k1': 'v1',
        }
        b = {
            'k1': 'v1',
            'k2': 'v2'
        }
        self.assertFalse(subdict_matches(a, b))

    def test_dict_matches_4(self):
        a = {
            'k1': 'v1',
            'k2': 'v4',
            'k3': 'v3'
        }
        b = {
            'k1': 'v1',
            'k2': 'v2'
        }
        self.assertFalse(subdict_matches(a, b))

    def test_dict_matches_graph(self):
        g = nx.MultiDiGraph()

        g.add_node(1)
        g.add_node(2)
        g.add_edge(1, 2, relation='yup')
        g.add_edge(1, 2, relation='nope')

        d = {'relation': 'yup'}

        self.assertTrue(utils.any_subdict_matches(g.edge[1][2], d))

    def test_check_stability_good(self):
        d = {
            'A': {1, 2, 3},
            'B': {4, 5, 6}
        }

        m = {
            'A': {
                1: ('B', 4),
                2: ('B', 5)
            }
        }

        self.assertTrue(check_stability(d, m))

    def test_check_stability_missingNs(self):
        d = {
            'A': {1, 2, 3},
            'B': {4, 5, 6}
        }

        m = {
            'C': {
                1: ('B', 4),
                2: ('B', 5)
            }
        }

        self.assertFalse(check_stability(d, m))

    def test_check_stability_MissingValue(self):
        d = {
            'A': {1, 2, 3},
            'B': {4, 5, 6}
        }

        m = {
            'A': {
                1: ('B', 4),
                0: ('B', 5)
            }
        }

        self.assertFalse(check_stability(d, m))

    def test_check_stability_MissingNsLink(self):
        d = {
            'A': {1, 2, 3},
            'B': {4, 5, 6}
        }

        m = {
            'A': {
                1: ('C', 4),
                2: ('B', 5)
            }
        }

        self.assertFalse(check_stability(d, m))

    def test_check_stability_MissingMapValue(self):
        d = {
            'A': {1, 2, 3},
            'B': {4, 5, 6}
        }

        m = {
            'A': {
                1: ('B', 4),
                2: ('B', 9)
            }
        }

        self.assertFalse(check_stability(d, m))

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
        self.assertEqual(expected, utils.flatten(d))

    def test_flatten_edges(self):
        g = nx.MultiDiGraph()
        g.add_edge(1, 2, key=5, attr_dict={'A': 'a', 'B': {'C': 'c', 'D': 'd'}})

        result = utils.flatten_edges(g)

        expected = nx.MultiDiGraph()
        expected.add_edge(1, 2, key=5, attr_dict={'A': 'a', 'B_C': 'c', 'B_D': 'd'})

        self.assertEqual(set(result.nodes()), set(expected.nodes()))

        res_edges = result.edges(keys=True)
        exp_edges = expected.edges(keys=True)
        self.assertEqual(set(res_edges), set(exp_edges))

        for u, v, k in expected.edges(keys=True):
            self.assertEqual(expected[u][v][k], result[u][v][k])
