# -*- coding: utf-8 -*-

import unittest

import networkx as nx

import pybel.utils
from pybel.canonicalize import postpend_location, decanonicalize_node
from pybel.constants import FUNCTION
from pybel.io.line_utils import split_file_to_annotations_and_definitions
from pybel.parser.language import amino_acid
from pybel.parser.parse_exceptions import PlaceholderAminoAcidWarning
from pybel.parser.utils import nest
from pybel.utils import get_bel_resource, list2tuple
from tests.constants import test_an_1, test_bel_simple
from tests.mocks import mock_bel_resources


class TestCanonicalizeHelper(unittest.TestCase):
    def test_postpend_location_failure(self):
        with self.assertRaises(ValueError):
            postpend_location('', dict(name='failure'))

    def test_decanonicalize_node_failure(self):
        class NotGraph:
            node = None

        x = NotGraph()

        test_node = ('nope', 'nope', 'nope')
        x.node = {test_node: {FUNCTION: 'nope'}}

        with self.assertRaises(ValueError):
            decanonicalize_node(x, test_node)


class TestRandom(unittest.TestCase):
    def test_nest_failure(self):
        with self.assertRaises(ValueError):
            nest()

    def test_bad_aminoAcid(self):
        with self.assertRaises(PlaceholderAminoAcidWarning):
            amino_acid.parseString('X')

    def test_split_lines(self):
        with open(test_bel_simple) as f:
            docs, definitions, statements = split_file_to_annotations_and_definitions(f)

        self.assertEqual(7, len(docs))
        self.assertEqual(4, len(definitions))
        self.assertEqual(14, len(statements))

    def test_list2tuple(self):
        l = [None, 1, 's', [1, 2, [4], [[]]]]
        e = (None, 1, 's', (1, 2, (4,), ((),)))
        t = list2tuple(l)

        self.assertEqual(t, e)


class TestUtils(unittest.TestCase):
    @mock_bel_resources
    def test_download_url(self, mock):
        res = get_bel_resource(test_an_1)

        expected_values = {
            'TestAnnot1': 'O',
            'TestAnnot2': 'O',
            'TestAnnot3': 'O',
            'TestAnnot4': 'O',
            'TestAnnot5': 'O'
        }

        self.assertEqual(expected_values, res['Values'])

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
        self.assertEqual(expected, pybel.utils.flatten_dict(d))

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
        self.assertEqual(expected, pybel.utils.flatten_dict(d))

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
