# -*- coding: utf-8 -*-

import logging
import unittest
from pathlib import Path

import pybel
from pybel.constants import *
from pybel.manager.cache import CacheManager
from pybel.manager.utils import parse_owl, OWLParser
from pybel.parser.language import belns_encodings
from pybel.parser.parse_metadata import MetadataParser
from tests.constants import mock_parse_owl_rdf, mock_bel_resources, mock_parse_owl_pybel, test_owl_ado
from tests.constants import test_bel_extensions, wine_iri, pizza_iri, test_owl_pizza, test_owl_wine, expected_test_bel_4_metadata, \
    assertHasNode, assertHasEdge, HGNC_KEYWORD, HGNC_URL

log = logging.getLogger('pybel')


EXPECTED_PIZZA_NODES = {
    'Pizza',
    'Topping',
    'CheeseTopping',
    'FishTopping',
    'MeatTopping',
    'TomatoTopping'
}

EXPECTED_PIZZA_EDGES = {
    ('CheeseTopping', 'Topping'),
    ('FishTopping', 'Topping'),
    ('MeatTopping', 'Topping'),
    ('TomatoTopping', 'Topping')
}

class TestOwlBase(unittest.TestCase):
    def assertHasNode(self, g, n, **kwargs):
        assertHasNode(self, n, g, **kwargs)

    def assertHasEdge(self, g, u, v, **kwargs):
        assertHasEdge(self, u, v, g, **kwargs)


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

    def test_file(self):
        owl = parse_owl(Path(test_owl_pizza).as_uri())
        self.assertEqual(EXPECTED_PIZZA_NODES, set(owl.nodes()))
        self.assertEqual(EXPECTED_PIZZA_EDGES, set(owl.edges()))

    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_url(self, m1, m2):
        owl = parse_owl(pizza_iri)
        self.assertEqual(pizza_iri, owl.iri)
        self.assertEqual(EXPECTED_PIZZA_NODES, set(owl.nodes()))
        self.assertEqual(EXPECTED_PIZZA_EDGES, set(owl.edges()))

    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_metadata_parser(self, m1, m2):
        functions = set('A')
        s = 'DEFINE NAMESPACE PIZZA AS OWL {} "{}"'.format(''.join(functions), pizza_iri)
        parser = MetadataParser(CacheManager('sqlite:///'))
        parser.parseString(s)

        self.assertIn('PIZZA', parser.namespace_dict)

        names = set(parser.namespace_dict['PIZZA'].keys())
        for node in EXPECTED_PIZZA_NODES:
            self.assertIn(node, names)
            self.assertEqual(functions, parser.namespace_dict['PIZZA'][node])

    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_metadata_parser_no_function(self, m1, m2):
        s = 'DEFINE NAMESPACE PIZZA AS OWL "{}"'.format(pizza_iri)
        parser = MetadataParser(CacheManager('sqlite:///'))
        parser.parseString(s)

        self.assertIn('PIZZA', parser.namespace_dict)

        functions = set(belns_encodings.keys())
        names = set(parser.namespace_dict['PIZZA'].keys())
        for node in EXPECTED_PIZZA_NODES:
            self.assertIn(node, names)
            self.assertEqual(functions, parser.namespace_dict['PIZZA'][node])

    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_metadata_parser_annotation(self, m1, m2):
        s = 'DEFINE ANNOTATION Pizza AS OWL "{}"'.format(pizza_iri)
        parser = MetadataParser(CacheManager('sqlite:///'))
        parser.parseString(s)

        self.assertIn('Pizza', parser.annotations_dict)
        self.assertEqual(EXPECTED_PIZZA_NODES, set(parser.annotations_dict['Pizza']))


class TestWine(TestOwlBase):
    def setUp(self):
        self.iri = wine_iri

        self.wine_expected_prefixes = {
            'owl': "http://www.w3.org/2002/07/owl#",
            'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        }

        self.wine_expected_classes = {
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

        self.wine_expected_individuals = {
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

        self.expected_nodes = self.wine_expected_classes | self.wine_expected_individuals

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
        owl = parse_owl(Path(test_owl_wine).as_uri())

        for node in sorted(self.wine_expected_classes):
            self.assertHasNode(owl, node)

        for node in sorted(self.wine_expected_individuals):
            self.assertHasNode(owl, node)

        for u, v in sorted(self.expected_subclasses):
            self.assertHasEdge(owl, u, v)

        for u, v in sorted(self.expected_membership):
            self.assertHasEdge(owl, u, v)

    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_metadata_parser_namespace(self, m1, m2):
        cm = CacheManager('sqlite://')

        functions = 'A'
        s = 'DEFINE NAMESPACE Wine AS OWL {} "{}"'.format(functions, wine_iri)

        parser = MetadataParser(cache_manager=cm)
        parser.parseString(s)

        self.assertIn('Wine', parser.namespace_dict)
        self.assertLessEqual(self.expected_nodes, set(parser.namespace_dict['Wine']))

        for node in sorted(self.expected_nodes):
            self.assertEqual(functions, ''.join(sorted(parser.namespace_dict['Wine'][node])))

        # Check nothing bad happens
        # with self.assertLogs('pybel', level='WARNING'):
        parser.parseString(s)

    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_metadata_parser_annotation(self, m1, m2):
        cm = CacheManager('sqlite://')
        s = 'DEFINE ANNOTATION Wine AS OWL "{}"'.format(wine_iri)

        parser = MetadataParser(cache_manager=cm)
        parser.parseString(s)

        self.assertIn('Wine', parser.annotations_dict)
        self.assertLessEqual(self.expected_nodes, set(parser.annotations_dict['Wine']))

        # Check nothing bad happens
        # with self.assertLogs('pybel', level='WARNING'):
        parser.parseString(s)


class TestAdo(TestOwlBase):
    ado_expected_nodes_subset = {
        'immunotherapy',
        'In_vitro_models',
        'white',
        'ProcessualEntity'
    }
    ado_expected_edges_subset = {
        ('control_trials_study_arm', 'Study_arm'),
        ('copper', 'MaterialEntity'),
        ('curcumin_plant', 'plant'),
        ('cytokine', 'cell_signalling')  # Line 12389 of ado.owl
    }

    def test_ado_local(self):
        ado_path = Path(test_owl_ado).as_uri()
        owl = parse_owl(ado_path)

        self.assertLessEqual(self.ado_expected_nodes_subset, set(owl.nodes_iter()))
        self.assertLessEqual(self.ado_expected_edges_subset, set(owl.edges_iter()))

    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_ado(self, mock1, mock2):
        ado_path = 'http://mock.com/ado.owl'
        owl = parse_owl(ado_path)

        self.assertLessEqual(self.ado_expected_nodes_subset, set(owl.nodes_iter()))
        self.assertLessEqual(self.ado_expected_edges_subset, set(owl.edges_iter()))


class TestOwlManager(unittest.TestCase):
    def setUp(self):
        self.manager = CacheManager()
        self.manager.drop_database()
        self.manager.create_database()

    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_ensure_namespace(self, m1, m2):
        self.manager.ensure_namespace_owl(pizza_iri)
        entries = self.manager.get_namespace_owl_terms(pizza_iri)
        self.assertEqual(EXPECTED_PIZZA_NODES, entries)

        edges = self.manager.get_namespace_owl_edges(pizza_iri)
        self.assertEqual(EXPECTED_PIZZA_EDGES, edges)

        # check nothing bad happens on second insert
        self.manager.ensure_namespace_owl(pizza_iri)

    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_ensure_annotation(self, m1, m2):
        self.manager.ensure_annotation_owl(pizza_iri)
        entries = self.manager.get_annotation_owl_terms(pizza_iri)
        self.assertEqual(EXPECTED_PIZZA_NODES, entries)

        edges = self.manager.get_annotation_owl_edges(pizza_iri)
        self.assertEqual(EXPECTED_PIZZA_EDGES, edges)

        # check nothing bad happens on second insert
        self.manager.ensure_annotation_owl(pizza_iri)

    def test_missing_namespace(self):
        with self.assertRaises(Exception):
            self.manager.ensure_namespace_owl('http://example.com/not_owl.owl')

    def test_insert_missing_namespace(self):
        with self.assertRaises(Exception):
            self.manager.insert_namespace_owl('http://cthoyt.com/not_owl.owl')

    def test_missing_annotation(self):
        with self.assertRaises(Exception):
            self.manager.ensure_annotation_owl('http://example.com/not_owl.owl')

    def test_insert_missing_annotation(self):
        with self.assertRaises(Exception):
            self.manager.insert_annotation_owl('http://cthoyt.com/not_owl.owl')


class TestIntegration(TestOwlBase):
    @mock_bel_resources
    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_from_path(self, m1, m2, m3):
        g = pybel.from_path(test_bel_extensions)
        self.assertEqual(0, len(g.warnings))

        self.assertEqual(expected_test_bel_4_metadata, g.document)

        expected_definitions = {
            HGNC_KEYWORD: HGNC_URL,
            'PIZZA': pizza_iri,
            'WINE': wine_iri
        }

        actual_definitions = {}
        actual_definitions.update(g.namespace_url)
        actual_definitions.update(g.namespace_owl)

        self.assertEqual(expected_definitions, actual_definitions)

        expected_annotations = {
            'Wine': wine_iri
        }

        actual_annotations = {}
        actual_annotations.update(g.annotation_url)
        actual_annotations.update(g.annotation_owl)

        self.assertEqual(expected_annotations, actual_annotations)

        a = PROTEIN, 'HGNC', 'AKT1'
        b = PROTEIN, 'HGNC', 'EGFR'
        self.assertHasNode(g, a)
        self.assertHasNode(g, b)
        self.assertHasEdge(g, a, b)

        annots = {
            CITATION: {
                CITATION_NAME:'That one article from last week',
                CITATION_REFERENCE: '123455',
                CITATION_TYPE:'PubMed'
            },
            EVIDENCE: 'Made up support, not even qualifying as evidence',
            ANNOTATIONS: {'Wine': 'Cotturi'}
        }
        self.assertHasEdge(g, (ABUNDANCE, "PIZZA", "MeatTopping"), (ABUNDANCE, 'WINE', 'Wine'), **annots)
        self.assertHasEdge(g, (ABUNDANCE, "PIZZA", "TomatoTopping"), (ABUNDANCE, 'WINE', 'Wine'), **annots)
        self.assertHasEdge(g, (ABUNDANCE, 'WINE', 'WhiteWine'), (ABUNDANCE, "PIZZA", "FishTopping"), **annots)
