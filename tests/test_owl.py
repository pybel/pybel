import os
import unittest

from pybel.utils import OWLParser
from tests.constants import dir_path

test_owl_1 = os.path.join(dir_path, 'owl', 'pizza_onto.owl')
test_owl_2 = os.path.join(dir_path, 'owl', 'wine.owl')


class TestOwlBase(unittest.TestCase):
    def assertHasNode(self, g, n):
        self.assertTrue(g.has_node(n), msg="Missing node: {}".format(n))

    def assertHasEdge(self, g, u, v):
        self.assertTrue(g.has_edge(u, v), msg="Missing edge: ({}, {})".format(u, v))


class TestOwlUtils(unittest.TestCase):
    def test_value_error(self):
        with self.assertRaises(ValueError):
            OWLParser()


class TestPizza(TestOwlBase):
    def setUp(self):
        self.expected_nodes = {
            'Pizza',
            'Topping',
            'CheeseTopping',
            'FishTopping',
            'MeatTopping',
            'TomatoTopping'
        }

        self.expected_edges = {
            ('CheeseTopping', 'Topping'),
            ('FishTopping', 'Topping'),
            ('MeatTopping', 'Topping'),
            ('TomatoTopping', 'Topping')
        }

    def test_file(self):
        owl = OWLParser(file=test_owl_1)

        self.assertEqual(owl.name_url, "http://www.lesfleursdunormal.fr/static/_downloads/pizza_onto.owl")

        for node in self.expected_nodes:
            self.assertHasNode(owl, node)

        for u, v in self.expected_edges:
            self.assertHasEdge(owl, u, v)


class TestWine(TestOwlBase):
    def setUp(self):
        # TODO add remaining items from hierarchy
        self.expected_nodes = {
            'WineDescriptor',
            'WineColor',
            'Red',
            'Rose',
            'White'
            'WineTaste',
            'WineBody',
            'Full',
            'Light',
            'Medium'
            'WineFlavor',
            'Delicate',
            'Moderate',
            'Strong'
            'WineSugar',
            'Dry',
            'OffDry',
            'Sweet'
        }

        self.expected_edges = [
            ('Dry', 'WineSugar'),
            ('OffDry', 'WineSugar'),
            ('Sweet', 'WineSugar'),
            ('WineSugar', 'WineTaste'),
            ('WineTaste', 'WineDescriptor'),
            ('Red', 'WineColor'),
            ('Rose', 'WineColor'),
            ('White', 'WineColor'),
            ('WineColor', 'WineDescriptor')
        ]

    def test_file(self):
        owl = OWLParser(file=test_owl_2)

        self.assertEqual(owl.name_url, "http://www.w3.org/TR/2003/PR-owl-guide-20031209/wine")

        for node in self.expected_nodes:
            self.assertHasNode(owl, node)

        for u, v in self.expected_edges:
            self.assertHasEdge(owl, u, v)

    def test_string(self):
        with open(test_owl_2) as f:
            owl = OWLParser(content=f.read())

        self.assertEqual(owl.name_url, "http://www.w3.org/TR/2003/PR-owl-guide-20031209/wine")

        for node in self.expected_nodes:
            self.assertHasNode(owl, node)

        for u, v in self.expected_edges:
            self.assertHasEdge(owl, u, v)
