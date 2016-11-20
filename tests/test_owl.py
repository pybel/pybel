import os
import unittest

from pybel.parser.parse_metadata import MetadataParser
from pybel.parser.utils import OWLParser, parse_owl

from tests.constants import dir_path

test_owl_1 = os.path.join(dir_path, 'owl', 'pizza_onto.owl')
test_owl_2 = os.path.join(dir_path, 'owl', 'wine.owl')

pizza_url = "http://www.lesfleursdunormal.fr/static/_downloads/pizza_onto.owl"
wine_url = "http://www.w3.org/TR/2003/PR-owl-guide-20031209/wine"


class TestOwlBase(unittest.TestCase):
    def assertHasNode(self, g, n):
        self.assertTrue(g.has_node(n), msg="Missing node: {}".format(n))

    def assertHasEdge(self, g, u, v):
        self.assertTrue(g.has_edge(u, v), msg="Missing edge: ({}, {})".format(u, v))


class TestOwlUtils(unittest.TestCase):
    def test_value_error(self):
        with self.assertRaises(ValueError):
            OWLParser()

# TODO parametrize tests

class TestPizza(TestOwlBase):
    def setUp(self):
        self.url = pizza_url

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

        self.assertEqual(self.url, owl.name_url)
        self.assertEqual(self.expected_nodes, set(owl.nodes()))
        self.assertEqual(self.expected_edges, set(owl.edges()))

    def test_url(self):
        owl = parse_owl(url=self.url)

        self.assertEqual(self.url, owl.name_url)
        self.assertEqual(self.expected_nodes, set(owl.nodes()))
        self.assertEqual(self.expected_edges, set(owl.edges()))

    def test_metadata_parser(self):
        functions = set('A')
        s = 'DEFINE NAMESPACE Pizza AS OWL {} "{}"'.format(''.join(functions), pizza_url)
        parser = MetadataParser()
        parser.parseString(s)

        names = set(parser.namespace_dict['Pizza'].keys())
        for node in self.expected_nodes:
            self.assertIn(node, names)
            self.assertEqual(functions, parser.namespace_dict['Pizza'][node])


class TestWine(TestOwlBase):
    def setUp(self):
        self.url = wine_url

        # TODO add remaining items from hierarchy
        self.expected_classes = {
            'ConsumableThing',
            'EdibleThing',
            'Dessert',
            'Fowl',
            'Meat',
            'NonSweetFruit',
            'OtherTomatoBasedFood',
            'Pasta',
            'Seafood',
            'SweetFruit',
            'Meal',
            'MealCourse',
            'PotableLiquid',
            'Juice',
            'Fruit',
            'NonConsumableThing',
            'Region',
            'Vintage',
            'VintageYear',
            'Wine'
            'WineDescriptor',
            'WineColor',
            'WineTaste',
            'WineBody',
            'WineFlavor',
            'WineSugar',
            'Winery'
        }

        self.expected_individuals = {
            'Red',
            'Rose',
            'White',
            'Full',
            'Light',
            'Medium',
            'Delicate',
            'Moderate',
            'Strong',
            'Dry',
            'OffDry',
            'Sweet',

            # Wineries
            'Bancroft',
            'Beringer',
            'ChateauChevalBlanc',
            'ChateauDeMeursault',
            'ChateauDYchem',
            'ChateauLafiteRothschild',
            'ChateauMargauxWinery',
            'ChateauMorgon',
            'ClosDeLaPoussie',
            'ClosDeVougeot',
            'CongressSprings',
            'Corbans',
            'CortonMontrachet',
            'Cotturi',
            'DAnjou',
            'Elyse',
            'Forman',
            'Foxen',
            'GaryFarrell',
            'Handley',
            'KalinCellars',
            'KathrynKennedy',
            'LaneTanner',
            'Longridge',
            'Marietta',
            'McGuinnesso',
            'Mountadam',
            'MountEdenVineyard',
            'PageMillWinery',
            'PeterMccoy',
            'PulignyMontrachet',
            'SantaCruzMountainVineyard',
            'SaucelitoCanyon',
            'SchlossRothermel',
            'SchlossVolrad',
            'SeanThackrey',
            'Selaks',
            'SevreEtMaine',
            'StGenevieve',
            'Stonleigh',
            'Taylor',
            'Ventana',
            'WhitehallLane'
        }

        self.expected_nodes = self.expected_classes | self.expected_individuals

        self.expected_subclasses = {

            ('WineSugar', 'WineTaste'),
            ('WineTaste', 'WineDescriptor'),
            ('WineColor', 'WineDescriptor')
        }

        self.expected_membership = {
            ('Red', 'WineColor'),
            ('Rose', 'WineColor'),
            ('White', 'WineColor'),
            ('Full', 'WineBody'),
            ('Light', 'WineBody'),
            ('Medium', 'WineBody'),
            ('Delicate', 'WineFlavor'),
            ('Moderate', 'WineFlavor'),
            ('Strong', 'WineFlavor'),
            ('Dry', 'WineSugar'),
            ('OffDry', 'WineSugar'),
            ('Sweet', 'WineSugar'),

            # Winery Membership
            ('Bancroft', 'Winery'),
            ('Beringer', 'Winery'),
            ('ChateauChevalBlanc', 'Winery'),
            ('ChateauDeMeursault', 'Winery'),
            ('ChateauDYchem', 'Winery'),
            ('ChateauLafiteRothschild', 'Winery'),
            ('ChateauMargauxWinery', 'Winery'),
            ('ChateauMorgon', 'Winery'),
            ('ClosDeLaPoussie', 'Winery'),
            ('ClosDeVougeot', 'Winery'),
            ('CongressSprings', 'Winery'),
            ('Corbans', 'Winery'),
            ('CortonMontrachet', 'Winery'),
            ('Cotturi', 'Winery'),
            ('DAnjou', 'Winery'),
            ('Elyse', 'Winery'),
            ('Forman', 'Winery'),
            ('Foxen', 'Winery'),
            ('GaryFarrell', 'Winery'),
            ('Handley', 'Winery'),
            ('KalinCellars', 'Winery'),
            ('KathrynKennedy', 'Winery'),
            ('LaneTanner', 'Winery'),
            ('Longridge', 'Winery'),
            ('Marietta', 'Winery'),
            ('McGuinnesso', 'Winery'),
            ('Mountadam', 'Winery'),
            ('MountEdenVineyard', 'Winery'),
            ('PageMillWinery', 'Winery'),
            ('PeterMccoy', 'Winery'),
            ('PulignyMontrachet', 'Winery'),
            ('SantaCruzMountainVineyard', 'Winery'),
            ('SaucelitoCanyon', 'Winery'),
            ('SchlossRothermel', 'Winery'),
            ('SchlossVolrad', 'Winery'),
            ('SeanThackrey', 'Winery'),
            ('Selaks', 'Winery'),
            ('SevreEtMaine', 'Winery'),
            ('StGenevieve', 'Winery'),
            ('Stonleigh', 'Winery'),
            ('Taylor', 'Winery'),
            ('Ventana', 'Winery'),
            ('WhitehallLane', 'Winery'),
        }

        self.expected_edges = self.expected_subclasses | self.expected_membership

    def test_file(self):
        owl = OWLParser(file=test_owl_2)

        self.assertEqual(self.url, owl.name_url)

        for node in sorted(self.expected_classes):
            self.assertHasNode(owl, node)

        for node in sorted(self.expected_individuals):
            self.assertHasNode(owl, node)

        for u, v in sorted(self.expected_subclasses):
            self.assertHasEdge(owl, u, v)

        for u, v in sorted(self.expected_membership):
            self.assertHasEdge(owl, u, v)


    def test_string(self):
        with open(test_owl_2) as f:
            owl = OWLParser(content=f.read())

        self.assertEqual(self.url, owl.name_url)

        for node in sorted(self.expected_classes):
            self.assertHasNode(owl, node)

        for node in sorted(self.expected_individuals):
            self.assertHasNode(owl, node)

        for u, v in sorted(self.expected_subclasses):
            self.assertHasEdge(owl, u, v)

        for u, v in sorted(self.expected_membership):
            self.assertHasEdge(owl, u, v)

    def test_metadata_parser(self):
        functions = 'A'
        s = 'DEFINE NAMESPACE Wine AS OWL {} "{}"'.format(functions, wine_url)
        parser = MetadataParser()
        parser.parseString(s)

        names = set(parser.namespace_dict['Wine'].keys())
        for node in sorted(self.expected_nodes):
            self.assertIn(node, names)
            self.assertEqual(functions, ''.join(sorted(parser.namespace_dict['Wine'][node])))
