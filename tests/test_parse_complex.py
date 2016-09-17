import unittest

from pybel.parsers.biological_statements import *


def sexpr_equal(exp1, exp2):
    if type(exp1) != type(exp2):
        return False
    if isinstance(exp1, list):
        if len(exp1) != len(exp2):
            return False
        for a, b in zip(exp1, exp2):
            if not sexpr_equal(a, b):
                return False
        return True
    else:
        return exp1 == exp2


class TestSexpr(unittest.TestCase):
    def test_atomic1(self):
        exp1 = 5
        exp2 = 7
        self.assertFalse(sexpr_equal(exp1, exp2))

    def test_atomic2(self):
        exp1 = 5
        exp2 = 5
        self.assertTrue(sexpr_equal(exp1, exp2))

    def test_atomic2(self):
        exp1 = 5.0
        exp2 = 5.0
        self.assertTrue(sexpr_equal(exp1, exp2))

    def test_atomic3(self):
        exp1 = 5.0
        exp2 = 7.0
        self.assertFalse(sexpr_equal(exp1, exp2))

    def test_atomic4(self):
        exp1 = 'hi'
        exp2 = 'hi'
        self.assertTrue(sexpr_equal(exp1, exp2))

    def test_atomic5(self):
        exp1 = 'hi'
        exp2 = 'hello'
        self.assertFalse(sexpr_equal(exp1, exp2))

    def test_list1(self):
        exp1 = [0]
        exp2 = [0]
        self.assertTrue(sexpr_equal(exp1, exp2))

    def test_list2(self):
        exp1 = [0, 1]
        exp2 = [0, 1]
        self.assertTrue(sexpr_equal(exp1, exp2))

    def test_list3(self):
        exp1 = [0]
        exp2 = [1]
        self.assertFalse(sexpr_equal(exp1, exp2))

    def test_list4(self):
        exp1 = [0, 1]
        exp2 = [0, 1, 2]
        self.assertFalse(sexpr_equal(exp1, exp2))

    def test_list5(self):
        exp1 = [0, 1]
        exp2 = [0, 2]
        self.assertFalse(sexpr_equal(exp1, exp2))

    def test_list6(self):
        exp1 = [0, 1]
        exp2 = [2, 1]
        self.assertFalse(sexpr_equal(exp1, exp2))


class TestComplex1(unittest.TestCase):
    def setUp(self):
        self.expected = [
            ['proteinAbundance', ['HGNC', 'CAT']],
            'decreases',
            [['abundance', ('CHEBI', 'hydrogen peroxide')],
             'increases',
             ['biologicalProcess', ['GO', 'apoptotic process']]]
        ]

    def test111(self):
        """This test check double edges"""
        statement = '''proteinAbundance(HGNC:CAT) decreases (abundance(CHEBI:"hydrogen peroxide") increases biologicalProcess(GO:"apoptotic process"))'''
        result = tokenize_statement(statement)
        self.assertTrue(sexpr_equal(self.expected, result))

    def test112(self):
        """This test check double edges, with added whitespaces"""
        statement = '''proteinAbundance(HGNC:CAT) decreases ( abundance(CHEBI:"hydrogen peroxide") increases biologicalProcess(GO:"apoptotic process") )'''
        result = tokenize_statement(statement)
        self.assertTrue(sexpr_equal(self.expected, result))


class TestComplex2(unittest.TestCase):
    def test121(self):
        """Test nested definitions"""
        statement = '''peptidaseActivity(complexAbundance(proteinAbundance(HGNC:F3),proteinAbundance(HGNC:F7))) directlyIncreases peptidaseActivity(proteinAbundance(HGNC:F9))'''
        result = tokenize_statement(statement)

        expected = [
            ['peptidaseActivity',
             ['complexAbundance',
              ['proteinAbundance', ['HGNC', 'F3']],
              ['proteinAbundance', ['HGNC', 'F7']]
              ]
             ],
            'directlyIncreases',
            ['peptidaseActivity', ['proteinAbundance', ['HGNC', 'F9']]]
        ]

        self.assertTrue(sexpr_equal(expected, result))


# TODO: should we use JSON instead of SEXPRS?
# TODO: what information is necessary in statement_info

class TestValidate(unittest.TestCase):
    def setUp(self):
        self.statement_info = {
            'proteinAbundance': {
                'nargs': 1,
            },
            'abundance': {
                'nargs': 1,
            },
            'biologicalProcess': {
                'nargs': 1
            },
            'complexAbundance': {
                'nargs': 2
            }
        }

        self.entity_info = {
            'HGNC': {'CAT', 'F3', 'F7', 'F9'},
            'CHEBI': {'hydrogen peroxide'},
            'GO': {'apoptotic process'}
        }

    def test111(self):
        sexpr = [
            ['proteinAbundance', ['HGNC', 'CAT']],
            'decreases',
            [['abundance', ('CHEBI', 'hydrogen peroxide')],
             'increases',
             ['biologicalProcess', ['GO', 'apoptotic process']]]
        ]

        valid = validate_sexpr(sexpr, self.statement_info, self.entity_info)
        self.assertTrue(valid)
