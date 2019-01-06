# -*- coding: utf-8 -*-

"""Tests for parsing utilities."""

import unittest

import networkx as nx

from pybel.utils import subdict_matches
from tests.constants import any_subdict_matches


class TestSubdictMatching(unittest.TestCase):
    """Tests for matching sub-dictionaries."""

    def test_dict_matches_1(self):
        target = {
            'k1': 'v1',
            'k2': 'v2'
        }
        query = {
            'k1': 'v1',
            'k2': 'v2'
        }
        self.assertTrue(subdict_matches(target, query))

    def test_dict_matches_2(self):
        target = {
            'k1': 'v1',
            'k2': 'v2',
            'k3': 'v3'
        }
        query = {
            'k1': 'v1',
            'k2': 'v2'
        }
        self.assertTrue(subdict_matches(target, query))

    def test_dict_matches_3(self):
        target = {
            'k1': 'v1',
        }
        query = {
            'k1': 'v1',
            'k2': 'v2'
        }
        self.assertFalse(subdict_matches(target, query))

    def test_dict_matches_4(self):
        target = {
            'k1': 'v1',
            'k2': 'v4',
            'k3': 'v3'
        }
        query = {
            'k1': 'v1',
            'k2': 'v2'
        }
        self.assertFalse(subdict_matches(target, query))

    def test_dict_matches_5(self):
        target = {
            'k1': 'v1',
            'k2': 'v2'
        }
        query = {
            'k1': 'v1',
            'k2': ['v2', 'v3']
        }
        self.assertTrue(subdict_matches(target, query))

    def test_dict_matches_6(self):
        target = {
            'k1': 'v1',
            'k2': ['v2', 'v3']
        }
        query = {
            'k1': 'v1',
            'k2': 'v4'
        }
        self.assertFalse(subdict_matches(target, query))

    def test_dict_matches_7_partial(self):
        """Tests a partial match"""
        target = {
            'k1': 'v1',
            'k2': 'v2'
        }
        query = {
            'k1': 'v1',
            'k2': {'v2': 'v3'}
        }

        self.assertFalse(subdict_matches(target, query))

    def test_dict_matches_7_exact(self):
        """Test a partial match."""
        target = {
            'k1': 'v1',
            'k2': 'v2'
        }
        query = {
            'k1': 'v1',
            'k2': {'v2': 'v3'}
        }

        self.assertFalse(subdict_matches(target, query, partial_match=False))

    def test_dict_matches_8_partial(self):
        """Test a partial match."""
        target = {
            'k1': 'v1',
            'k2': {'v2': 'v3', 'v4': 'v5'}
        }
        query = {
            'k1': 'v1',
            'k2': {'v2': 'v3'}
        }

        self.assertTrue(subdict_matches(target, query))

    def test_dict_matches_graph(self):
        """Test matching a graph."""
        g = nx.MultiDiGraph()

        g.add_node(1)
        g.add_node(2)
        g.add_edge(1, 2, relation='yup')
        g.add_edge(1, 2, relation='nope')

        d = {'relation': 'yup'}

        self.assertTrue(any_subdict_matches(g[1][2], d))
