import os
import unittest

import networkx as nx

from pybel.parser import utils
from pybel.parser.utils import subdict_matches, check_stability, sanitize_file_lines

dir_path = os.path.dirname(os.path.realpath(__file__))


class TestUtils(unittest.TestCase):
    def test_list2tuple(self):
        l = [None, 1, 's', [1, 2, [4], [[]]]]
        e = (None, 1, 's', (1, 2, (4,), ((),)))
        t = utils.list2tuple(l)

        self.assertEqual(t, e)

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

    def test_dict_matches_5(self):
        a = {
            'k1': 'v1',
            'k2': 'v2'
        }
        b = {
            'k1': 'v1',
            'k2': ['v2', 'v3']
        }
        self.assertTrue(subdict_matches(a, b))

    def test_dict_matches_6(self):
        a = {
            'k1': 'v1',
            'k2': ['v2', 'v3']
        }
        b = {
            'k1': 'v1',
            'k2': 'v4'
        }
        self.assertFalse(subdict_matches(a, b))

    def test_dict_matches_7(self):
        a = {
            'k1': 'v1',
            'k2': 'v2'
        }
        b = {
            'k1': 'v1',
            'k2': {'v2': 'v3'}
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

    def test_cartesian_dictionary(self):
        d = {
            'A': {'1', '2'},
            'B': {'x', 'y', 'z'}
        }
        results = utils.cartesian_dictionary(d)

        expected_results = [
            {'A': '1', 'B': 'x'},
            {'A': '1', 'B': 'y'},
            {'A': '1', 'B': 'z'},
            {'A': '2', 'B': 'x'},
            {'A': '2', 'B': 'y'},
            {'A': '2', 'B': 'z'},
        ]

        for result in results:
            found = False
            for expected_result in expected_results:
                if result == expected_result:
                    found = True
            self.assertTrue(found)


class TestSanitize(unittest.TestCase):
    def test_a(self):
        s = '''SET Evidence = "The phosphorylation of S6K at Thr389, which is the TORC1-mediated site, was not inhibited
in the SIN1-/- cells (Figure 5A)."'''.split('\n')

        expect = [
            (1,
             'SET Evidence = "The phosphorylation of S6K at Thr389, which is the TORC1-mediated site, was not inhibited '
             'in the SIN1-/- cells (Figure 5A)."')]
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
             'SET Evidence = "Here we show that interfereon-alpha (IFNalpha) is a potent producer of SOCS expression in '
             'human T cells, as high expression of CIS, SOCS-1, SOCS-2, and SOCS-3 was detectable after IFNalpha '
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
        path = os.path.join(dir_path, 'bel', 'test_bel_1.bel')

        with open(path) as f:
            lines = list(sanitize_file_lines(f))

        self.assertEqual(26, len(lines))

    def test_f(self):
        s = '''SET Evidence = "Arterial cells are highly susceptible to oxidative stress, which can induce both necrosis
and apoptosis (programmed cell death) [1,2]"'''.split('\n')
        lines = list(sanitize_file_lines(s))
        self.assertEqual(1, len(lines))

    def test_quote(self):
        a = "word1 word2"
        self.assertEqual('"word1 word2"', utils.ensure_quotes(a))

        b = "word1"
        self.assertEqual('word1', utils.ensure_quotes(b))

        c = "word1$#"
        self.assertEqual('"word1$#"', utils.ensure_quotes(c))
