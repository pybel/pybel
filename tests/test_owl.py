# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import unittest
from pathlib import Path

from pybel import from_path
from pybel.constants import *
from pybel.manager.utils import parse_owl, OWLParser
from pybel.parser.parse_exceptions import RedefinedAnnotationError, RedefinedNamespaceError
from pybel.parser.parse_metadata import MetadataParser
from tests.constants import (
    FleetingTemporaryCacheMixin,
    TestGraphMixin,
    test_bel_extensions,
    wine_iri,
    pizza_iri,
    test_owl_pizza,
    test_owl_wine,
    expected_test_bel_4_metadata,
    HGNC_URL,
    test_owl_ado
)
from tests.mocks import mock_bel_resources, mock_parse_owl_pybel, mock_parse_owl_rdf

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

wine_prefixes = {
    'owl': "http://www.w3.org/2002/07/owl#",
    'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
}

wine_classes = {
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

wine_individuals = {
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

wine_nodes = wine_classes | wine_individuals

wine_subclasses = {

    ('WineSugar', 'WineTaste'),
    ('WineTaste', 'WineDescriptor'),
    ('WineColor', 'WineDescriptor')
}

wine_membership = {
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

wine_edges = wine_subclasses | wine_membership

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

expected_prefixes = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "owl": "http://www.w3.org/2002/07/owl#"
}


class TestOwlUtils(unittest.TestCase):
    def test_value_error(self):
        with self.assertRaises(ValueError):
            OWLParser()

    def test_invalid_owl(self):
        with self.assertRaises(Exception):
            parse_owl('http://example.com/not_owl')


class TestParse(TestGraphMixin):
    """This class tests the parsing of OWL documents and doesn't need a connection"""

    def test_parse_pizza_file(self):
        owl = parse_owl(Path(test_owl_pizza).as_uri())
        self.assertEqual(EXPECTED_PIZZA_NODES, set(owl.nodes()))
        self.assertEqual(EXPECTED_PIZZA_EDGES, set(owl.edges()))

    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_parse_pizza_url(self, m1, m2):
        owl = parse_owl(pizza_iri)
        self.assertEqual(pizza_iri, owl.graph['IRI'])
        self.assertEqual(EXPECTED_PIZZA_NODES, set(owl.nodes()))
        self.assertEqual(EXPECTED_PIZZA_EDGES, set(owl.edges()))

    def test_parse_wine_file(self):
        owl = parse_owl(Path(test_owl_wine).as_uri())

        for node in sorted(wine_classes):
            self.assertHasNode(owl, node)

        for node in sorted(wine_individuals):
            self.assertHasNode(owl, node)

        for u, v in sorted(wine_subclasses):
            self.assertHasEdge(owl, u, v)

        for u, v in sorted(wine_membership):
            self.assertHasEdge(owl, u, v)

    def test_ado_local(self):
        ado_path = Path(test_owl_ado).as_uri()
        owl = parse_owl(ado_path)

        self.assertLessEqual(ado_expected_nodes_subset, set(owl.nodes_iter()))
        self.assertLessEqual(ado_expected_edges_subset, set(owl.edges_iter()))

    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_ado(self, mock1, mock2):
        ado_path = 'http://mock.com/ado.owl'
        owl = parse_owl(ado_path)
        self.assertLessEqual(ado_expected_nodes_subset, set(owl.nodes_iter()))
        self.assertLessEqual(ado_expected_edges_subset, set(owl.edges_iter()))


class TestParsePizza(TestGraphMixin, FleetingTemporaryCacheMixin):
    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_metadata_parse_pizza_namespace(self, m1, m2):
        functions = set('A')
        s = 'DEFINE NAMESPACE PIZZA AS OWL {} "{}"'.format(''.join(functions), pizza_iri)
        parser = MetadataParser(self.manager)
        parser.parseString(s)

        self.assertIn('PIZZA', parser.namespace_dict)

        names = set(parser.namespace_dict['PIZZA'].keys())
        for node in EXPECTED_PIZZA_NODES:
            self.assertIn(node, names)
            self.assertEqual(functions, parser.namespace_dict['PIZZA'][node])

    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_metadata_parser_pizza_namespace_no_function(self, m1, m2):
        s = 'DEFINE NAMESPACE PIZZA AS OWL "{}"'.format(pizza_iri)
        parser = MetadataParser(self.manager)
        parser.parseString(s)

        self.assertIn('PIZZA', parser.namespace_dict)

        functions = set(belns_encodings.keys())
        names = set(parser.namespace_dict['PIZZA'].keys())
        for node in EXPECTED_PIZZA_NODES:
            self.assertIn(node, names)
            self.assertEqual(functions, parser.namespace_dict['PIZZA'][node])

    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_metadata_parse_pizza_annotation(self, m1, m2):
        s = 'DEFINE ANNOTATION Pizza AS OWL "{}"'.format(pizza_iri)
        parser = MetadataParser(self.manager)
        parser.parseString(s)

        self.assertIn('Pizza', parser.annotations_dict)
        self.assertEqual(EXPECTED_PIZZA_NODES, set(parser.annotations_dict['Pizza']))


class TestWine(TestGraphMixin, FleetingTemporaryCacheMixin):
    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_metadata_parse_wine_namespace(self, m1, m2):
        functions = 'A'
        s = 'DEFINE NAMESPACE Wine AS OWL {} "{}"'.format(functions, wine_iri)

        parser = MetadataParser(self.manager)
        parser.parseString(s)

        self.assertIn('Wine', parser.namespace_dict)
        self.assertLessEqual(wine_nodes, set(parser.namespace_dict['Wine']))

        for node in sorted(wine_nodes):
            self.assertEqual(functions, ''.join(sorted(parser.namespace_dict['Wine'][node])))

        with self.assertRaises(RedefinedNamespaceError):
            parser.parseString(s)

    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_metadata_parse_wine_annotation(self, m1, m2):
        s = 'DEFINE ANNOTATION Wine AS OWL "{}"'.format(wine_iri)

        parser = MetadataParser(self.manager)
        parser.parseString(s)

        self.assertIn('Wine', parser.annotations_dict)
        self.assertLessEqual(wine_nodes, set(parser.annotations_dict['Wine']))

        with self.assertRaises(RedefinedAnnotationError):
            parser.parseString(s)


class TestOwlManager(TestGraphMixin, FleetingTemporaryCacheMixin):
    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_ensure_pizza_namespace(self, m1, m2):
        self.manager.ensure_namespace_owl(pizza_iri)

        entries = self.manager.get_namespace_owl_terms(pizza_iri)
        self.assertEqual(EXPECTED_PIZZA_NODES, set(entries))

        edges = self.manager.get_namespace_owl_edges(pizza_iri)
        self.assertEqual(EXPECTED_PIZZA_EDGES, edges)

        # check nothing bad happens on second insert
        self.manager.ensure_namespace_owl(pizza_iri)

    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_ensure_pizza_annotation(self, m1, m2):
        self.manager.ensure_annotation_owl(pizza_iri)

        entries = self.manager.get_annotation_owl_terms(pizza_iri)
        self.assertEqual(EXPECTED_PIZZA_NODES, set(entries))

        edges = self.manager.get_annotation_owl_edges(pizza_iri)
        self.assertEqual(EXPECTED_PIZZA_EDGES, edges)

        # check nothing bad happens on second insert
        self.manager.ensure_annotation_owl(pizza_iri)

    def test_missing_namespace(self):
        with self.assertRaises(Exception):
            self.manager.ensure_namespace_owl('http://example.com/not_owl_namespace.owl')

    def test_missing_annotation(self):
        with self.assertRaises(Exception):
            self.manager.ensure_annotation_owl('http://example.com/not_owl_annotation.owl')


class TestExtensionIo(TestGraphMixin, FleetingTemporaryCacheMixin):
    """Tests the import of the test bel document with OWL extensions works properly"""

    @mock_bel_resources
    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_from_path(self, m1, m2, m3):
        graph = from_path(test_bel_extensions, manager=self.manager)
        self.assertEqual(0, len(graph.warnings))

        self.assertEqual(expected_test_bel_4_metadata, graph.document)

        self.assertEqual({
            'WINE': wine_iri,
            'PIZZA': 'http://www.lesfleursdunormal.fr/static/_downloads/pizza_onto.owl'
        }, graph.namespace_owl)
        self.assertEqual({'Wine': wine_iri}, graph.annotation_owl)
        self.assertEqual({'HGNC': HGNC_URL}, graph.namespace_url)

        a = PROTEIN, 'HGNC', 'AKT1'
        b = PROTEIN, 'HGNC', 'EGFR'
        self.assertHasNode(graph, a)
        self.assertHasNode(graph, b)
        self.assertHasEdge(graph, a, b)

        annots = {
            CITATION: {
                CITATION_NAME: 'That one article from last week',
                CITATION_REFERENCE: '123455',
                CITATION_TYPE: 'PubMed'
            },
            EVIDENCE: 'Made up support, not even qualifying as evidence',
            ANNOTATIONS: {'Wine': 'Cotturi'}
        }
        self.assertHasEdge(graph, (ABUNDANCE, "PIZZA", "MeatTopping"), (ABUNDANCE, 'WINE', 'Wine'), **annots)
        self.assertHasEdge(graph, (ABUNDANCE, "PIZZA", "TomatoTopping"), (ABUNDANCE, 'WINE', 'Wine'), **annots)
        self.assertHasEdge(graph, (ABUNDANCE, 'WINE', 'WhiteWine'), (ABUNDANCE, "PIZZA", "FishTopping"), **annots)


if __name__ == '__main__':
    unittest.main()
