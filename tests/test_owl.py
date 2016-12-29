import logging
import unittest

import requests.exceptions
from sqlalchemy import Table, MetaData

import pybel
from pybel.manager.cache import CacheManager
from pybel.manager.models import OWL_TABLE_NAME
from pybel.manager.utils import parse_owl, OWLParser
from pybel.parser.language import value_map
from pybel.parser.parse_metadata import MetadataParser
from tests.constants import test_bel_4, wine_iri, pizza_iri, test_owl_1, test_owl_2, test_owl_3

log = logging.getLogger('pybel')


class TestOwlBase(unittest.TestCase):
    def assertHasNode(self, g, n):
        self.assertTrue(g.has_node(n), msg="Missing node: {}".format(n))

    def assertHasEdge(self, g, u, v):
        self.assertTrue(g.has_edge(u, v), msg="Missing edge: ({}, {})".format(u, v))


class TestOwlUtils(unittest.TestCase):
    def test_value_error(self):
        with self.assertRaises(ValueError):
            OWLParser()

    def test_invalid_owl(self):
        with self.assertRaises(Exception):
            parse_owl('http://example.com/not_owl')


class TestParsePizza(TestOwlBase):
    expected_prefixes = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "owl": "http://www.w3.org/2002/07/owl#"
    }

    expected_nodes = {
        'Pizza',
        'Topping',
        'CheeseTopping',
        'FishTopping',
        'MeatTopping',
        'TomatoTopping'
    }

    expected_edges = {
        ('CheeseTopping', 'Topping'),
        ('FishTopping', 'Topping'),
        ('MeatTopping', 'Topping'),
        ('TomatoTopping', 'Topping')
    }

    def test_file(self):
        owl = parse_owl('file://' + test_owl_1)
        self.assertEqual(self.expected_nodes, set(owl.nodes()))
        self.assertEqual(self.expected_edges, set(owl.edges()))

    def test_url(self):
        owl = parse_owl(pizza_iri)

        self.assertEqual(pizza_iri, owl.iri)
        self.assertEqual(self.expected_nodes, set(owl.nodes()))
        self.assertEqual(self.expected_edges, set(owl.edges()))

    def test_metadata_parser(self):
        functions = set('A')
        s = 'DEFINE NAMESPACE Pizza AS OWL {} "{}"'.format(''.join(functions), pizza_iri)
        parser = MetadataParser(CacheManager('sqlite:///'))

        try:
            parser.parseString(s)
        except requests.exceptions.ConnectionError as e:
            log.warning('Connection Error %s', e)
            return

        names = set(parser.namespace_dict['Pizza'].keys())
        for node in self.expected_nodes:
            self.assertIn(node, names)
            self.assertEqual(functions, parser.namespace_dict['Pizza'][node])

    def test_metadata_parser_no_function(self):
        s = 'DEFINE NAMESPACE Pizza AS OWL "{}"'.format(pizza_iri)
        parser = MetadataParser(CacheManager('sqlite:///'))

        try:
            parser.parseString(s)
        except requests.exceptions.ConnectionError as e:
            log.warning('Connection Error %s', e)
            return

        functions = set(value_map.keys())
        names = set(parser.namespace_dict['Pizza'].keys())
        for node in self.expected_nodes:
            self.assertIn(node, names)
            self.assertEqual(functions, parser.namespace_dict['Pizza'][node])


class TestWine(TestOwlBase):
    def setUp(self):
        self.iri = wine_iri

        self.expected_prefixes = {
            'owl': "http://www.w3.org/2002/07/owl#",
            'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        }

        self.expected_classes = {
            'Region',
            'Vintage',
            'VintageYear',
            'Wine',
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
            'WhitehallLane',

            # Wines
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
        owl = parse_owl('file://' + test_owl_2)

        for node in sorted(self.expected_classes):
            self.assertHasNode(owl, node)

        for node in sorted(self.expected_individuals):
            self.assertHasNode(owl, node)

        for u, v in sorted(self.expected_subclasses):
            self.assertHasEdge(owl, u, v)

        for u, v in sorted(self.expected_membership):
            self.assertHasEdge(owl, u, v)

    def test_metadata_parser(self):
        cm = CacheManager('sqlite://')
        metadata = MetaData(cm.engine)
        table = Table(OWL_TABLE_NAME, metadata, autoload=True)
        self.assertIsNotNone(table)

        functions = 'A'
        s = 'DEFINE NAMESPACE Wine AS OWL {} "{}"'.format(functions, wine_iri)

        parser = MetadataParser(cm)

        try:
            parser.parseString(s)
        except ConnectionError as e:
            log.warning('Connection Error %s', e)
            return

        self.assertIn('Wine', parser.namespace_dict)
        names = sorted(parser.namespace_dict['Wine'].keys())
        for node in sorted(self.expected_nodes):
            self.assertIn(node, names)
            self.assertEqual(functions, ''.join(sorted(parser.namespace_dict['Wine'][node])))


class TestAdo(TestOwlBase):
    expected_nodes_subset = {
        'immunotherapy',
        'In_vitro_models',
        'white',
        'ProcessualEntity'
    }
    expected_edges_subset = {
        ('control_trials_study_arm', 'Study_arm'),
        ('copper', 'MaterialEntity'),
        ('curcumin_plant', 'plant'),
        ('cytokine', 'cell_signalling')  # Line 12389 of ado.owl
    }

    def test_ado(self):
        owl = parse_owl('file://' + test_owl_3)

        self.assertLessEqual(self.expected_nodes_subset, set(owl.nodes_iter()))
        self.assertLessEqual(self.expected_edges_subset, set(owl.edges_iter()))


class TestOwlManager(unittest.TestCase):
    def setUp(self):
        self.manager = CacheManager()
        self.manager.drop_database()
        self.manager.create_database()

    def test_insert(self):
        owl = parse_owl(pizza_iri)
        self.manager.insert_by_graph(pizza_iri, owl)
        entries = self.manager.get_owl_terms(pizza_iri)
        self.assertEqual(TestParsePizza.expected_nodes, entries)

        # get edges out
        edges = self.manager.get_edges(pizza_iri)

        self.assertEqual(TestParsePizza.expected_edges, edges)

        # check nothing bad happens on second insert
        self.manager.insert_by_graph(pizza_iri, owl)

    def test_missing(self):
        with self.assertRaises(Exception):
            self.manager.ensure_owl('http://example.com/not_owl.owl')

    def test_insert_missing(self):
        with self.assertRaises(Exception):
            self.manager.insert_by_iri('http://cthoyt.com/not_owl.owl')


class TestIntegration(TestOwlBase):
    def test_from_path(self):
        g = pybel.from_path(test_bel_4)

        expected_document = dict(
            Name="PyBEL Test Document 4",
            Description="Tests the use of OWL ontologies as namespaces",
            Version="1.6",
            Copyright="Copyright (c) Charles Tapley Hoyt. All Rights Reserved.",
            Authors="Charles Tapley Hoyt",
            Licenses="WTF License",
            ContactInfo="charles.hoyt@scai.fraunhofer.de",
        )

        expected_definitions = dict(
            HGNC="http://resource.belframework.org/belframework/1.0/namespace/hgnc-approved-symbols.belns",
            PIZZA="http://www.lesfleursdunormal.fr/static/_downloads/pizza_onto.owl",
            WINE="http://www.w3.org/TR/2003/PR-owl-guide-20031209/wine"
        )

        self.assertEqual(expected_document, g.document)

        actual_definitions = {}
        actual_definitions.update(g.namespace_url)
        actual_definitions.update(g.namespace_owl)

        self.assertEqual(expected_definitions, actual_definitions)

        a = 'Protein', 'HGNC', 'AKT1'
        b = 'Protein', 'HGNC', 'EGFR'
        self.assertHasNode(g, a)
        self.assertHasNode(g, b)
        self.assertHasEdge(g, a, b)

        self.assertHasEdge(g, ('Abundance', "PIZZA", "MeatTopping"), ('Abundance', 'WINE', 'Wine'))
        self.assertHasEdge(g, ('Abundance', "PIZZA", "TomatoTopping"), ('Abundance', 'WINE', 'Wine'))
        self.assertHasEdge(g, ('Abundance', 'WINE', 'WhiteWine'), ('Abundance', "PIZZA", "FishTopping"))
