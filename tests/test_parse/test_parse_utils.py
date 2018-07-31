# -*- coding: utf-8 -*-

"""Tests for parsing utilities."""

import unittest

import networkx as nx

from pybel.resources.document import sanitize_file_lines
from pybel.testing.constants import test_bel_simple
from pybel.utils import ensure_quotes, subdict_matches
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

        self.assertTrue(any_subdict_matches(g.edge[1][2], d))


class TestSanitize(unittest.TestCase):
    def test_a(self):
        s = '''SET Evidence = "The phosphorylation of S6K at Thr389, which is the TORC1-mediated site, was not inhibited
in the SIN1-/- cells (Figure 5A)."'''.split('\n')

        expect = [
            (1,
             'SET Evidence = "The phosphorylation of S6K at Thr389, which is the TORC1-mediated site, was not '
             'inhibited in the SIN1-/- cells (Figure 5A)."')]
        result = list(sanitize_file_lines(s))
        self.assertEqual(expect, result)

    def test_b(self):
        s = [
            '# Set document-defined annotation values\n',
            'SET Species = 9606',
            'SET Tissue = "t-cells"',
            '# Create an Evidence Line for a block of BEL Statements',
            'SET Evidence = "Here we show that interfereon-alpha (IFNalpha) is a potent producer \\',
            'of SOCS expression in human T cells, as high expression of CIS, SOCS-1, SOCS-2, \\',
            'and SOCS-3 was detectable after IFNalpha stimulation. After 4 h of stimulation \\',
            'CIS, SOCS-1, and SOCS-3 had ret'
        ]

        result = list(sanitize_file_lines(s))

        expect = [
            (2, 'SET Species = 9606'),
            (3, 'SET Tissue = "t-cells"'),
            (5,
             'SET Evidence = "Here we show that interfereon-alpha (IFNalpha) is a potent producer of SOCS expression '
             'in human T cells, as high expression of CIS, SOCS-1, SOCS-2, and SOCS-3 was detectable after IFNalpha '
             'stimulation. After 4 h of stimulation CIS, SOCS-1, and SOCS-3 had ret')
        ]

        self.assertEqual(expect, result)

    def test_c(self):
        s = [
            'SET Evidence = "yada yada yada" //this is a comment'
        ]

        result = list(sanitize_file_lines(s))
        expect = [(1, 'SET Evidence = "yada yada yada"')]

        self.assertEqual(expect, result)

    def test_d(self):
        """Test forgotten delimiters"""
        s = [
            'SET Evidence = "Something',
            'or other',
            'or other"'
        ]

        result = list(sanitize_file_lines(s))
        expect = [(1, 'SET Evidence = "Something or other or other"')]

        self.assertEqual(expect, result)

    def test_e(self):
        with open(test_bel_simple) as f:
            lines = list(sanitize_file_lines(f))

        self.assertEqual(26, len(lines))

    def test_f(self):
        s = '''SET Evidence = "Arterial cells are highly susceptible to oxidative stress, which can induce both necrosis
and apoptosis (programmed cell death) [1,2]"'''.split('\n')
        lines = list(sanitize_file_lines(s))
        self.assertEqual(1, len(lines))

    def test_quote(self):
        a = "word1 word2"
        self.assertEqual('"word1 word2"', ensure_quotes(a))

        b = "word1"
        self.assertEqual('word1', ensure_quotes(b))

        c = "word1$#"
        self.assertEqual('"word1$#"', ensure_quotes(c))
