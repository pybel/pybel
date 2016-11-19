import os
import unittest

from pybel.utils import OWLParser
from tests.constants import dir_path

test_owl_1 = os.path.join(dir_path, 'owl', 'pizza_onto.owl')
test_owl_2 = os.path.join(dir_path, 'owl', 'wine.owl')


class TestOwl(unittest.TestCase):
    def assertHasNode(self, g, n):
        self.assertTrue(g.has_node(n), msg="Missing node: {}".format(n))

    def assertHasEdge(self, g, u, v):
        self.assertTrue(g.has_edge(u, v), msg="Missing edge: ({}, {})".format(u, v))

    def test_pizza(self):
        owl = OWLParser(test_owl_1)

        self.assertEqual(owl.name_url, "http://www.lesfleursdunormal.fr/static/_downloads/pizza_onto.owl")

        # print(owl.nodes())
        # print(owl.edges())

        self.assertHasNode(owl, 'Pizza')
        self.assertHasNode(owl, 'Topping')
        self.assertHasNode(owl, 'CheeseTopping')
        self.assertHasEdge(owl, 'CheeseTopping', 'Topping')
        self.assertHasNode(owl, 'FishTopping')
        self.assertHasEdge(owl, 'FishTopping', 'Topping')
        self.assertHasNode(owl, 'MeatTopping')
        self.assertHasEdge(owl, 'MeatTopping', 'Topping')
        self.assertHasNode(owl, 'TomatoTopping')
        self.assertHasEdge(owl, 'TomatoTopping', 'Topping')

    def test_wine(self):
        owl = OWLParser(test_owl_2)

        self.assertEqual(owl.name_url, "http://www.w3.org/TR/2003/PR-owl-guide-20031209/wine")

        # TODO add remaining items from hierarchy
        expected_nodes = {
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

        expected_edges = [
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

        for node in expected_nodes:
            self.assertHasNode(owl, node)

        for u, v in expected_edges:
            self.assertHasEdge(owl, u, v)
