import unittest

from pybel import parsers


from pybel.parsers.set_statements import sanitize_statement_lines

class TestParseEvidence(unittest.TestCase):
    def test_111(self):
        statement = '''SET Evidence = "1.1.1 Easy case"'''
        expect = '''SET Evidence = "1.1.1 Easy case'''
        lines = sanitize_statement_lines(statement.split('\n'))
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertTrue(expect, line)

    def test_121(self):
        statement = '''SET Evidence = "1.2.1 Forward slash break test/
second line"'''
        expect = '''SET Evidence = "1.2.1 Forward slash break test second line"'''
        lines = sanitize_statement_lines(statement.split('\n'))
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertEqual(expect, line)

    def test_122(self):
        statement = '''SET Evidence = "1.2.2 Forward slash break test with whitespace /
second line"'''
        expect = '''SET Evidence = "1.2.2 Forward slash break test with whitespace second line"'''
        lines = sanitize_statement_lines(statement.split('\n'))
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertEqual(expect, line)

    def test_123(self):
        statement = '''SET Evidence = "1.2.3 Forward slash break test/
second line/
third line"'''
        expect = '''SET Evidence = "1.2.3 Forward slash break test second line third line"'''

        lines = sanitize_statement_lines(statement.split('\n'))
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertEqual(expect, line)

    def test_131(self):
        statement = '''SET Evidence = "3.1 Backward slash break test\\
second line"'''
        expect = '''SET Evidence = "3.1 Backward slash break test second line"'''
        lines = sanitize_statement_lines(statement.split('\n'))
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertEqual(expect, line)

    def test_132(self):
        statement = '''SET Evidence = "3.2 Backward slash break test with whitespace \\
second line"'''
        expect = '''SET Evidence = "3.2 Backward slash break test with whitespace second line"'''
        lines = sanitize_statement_lines(statement.split('\n'))
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertEqual(expect, line)

    def test_133(self):
        statement = '''SET Evidence = "3.3 Backward slash break test\\
second line\\
third line"'''
        expect = '''SET Evidence = "3.3 Backward slash break test second line third line"'''
        lines = sanitize_statement_lines(statement.split('\n'))
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertEqual(expect, line)

    def test_141(self):
        statement = '''SET Evidence = "4.1 Malformed line breakcase
second line"'''
        expect = '''SET Evidence = "4.1 Malformed line breakcase second line"'''
        lines = sanitize_statement_lines(statement.split('\n'))
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertEqual(expect, line)

    def test_142(self):
        statement = '''SET Evidence = "4.2 Malformed line breakcase
second line
third line"'''
        expect = '''SET Evidence = "4.2 Malformed line breakcase second line third line"'''
        lines = sanitize_statement_lines(statement.split('\n'))
        self.assertEqual(1, len(lines))
        line = lines[0]
        self.assertEqual(expect, line)


class TestParseCitation(unittest.TestCase):
    def test111(self):
        s = '''{"PubMed","Anti-neuroinflammatory effects of the calcium channel blocker nicardipine on microglial cells: implications for neuroprotection.","PloS one; Vol. 9; Iss. 3","2014-01-01","Bor-Ren Huang|Pei-Chun Chang|Wei-Lan Yeh|Chih-Hao Lee|Cheng-Fang Tsai|Chingju Lin|Hsiao-Yun Lin|Yu-Shu Liu|Caren Yu-Ju Wu|Pei-Ying Ko|Shiang-Suo Huang|Horng-Chaung Hsu|Dah-Yuu Lu","24621589"}'''


class TestParseDefinitions(unittest.TestCase):
    pass



