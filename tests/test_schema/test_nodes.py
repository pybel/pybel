import unittest

from pybel import schema as pbs
from pybel.dsl import Protein

n1 = Protein('HGNC', 'YFG')


class TestNodeSchema(unittest.TestCase):
    def test_simple(self):
        self.assertTrue(pbs.validate_node(n1))
