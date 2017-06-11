# -*- coding: utf-8 -*-

import os
from pathlib import Path

from pybel.manager import models
from pybel.manager.cache import CacheManager
from tests.constants import (
    FleetingTemporaryCacheMixin,
    HGNC_URL,
    help_check_hgnc,
    CELL_LINE_URL,
    HGNC_KEYWORD,
    test_eq_1,
    test_eq_2,
    belns_dir_path,
    test_ns_nocache,
    wine_iri
)
from tests.mocks import mock_bel_resources, mock_parse_owl_rdf, mock_parse_owl_pybel

ns1 = Path(os.path.join(belns_dir_path, 'disease-ontology.belns')).as_uri()
ns1_eq = Path(test_eq_1).as_uri()
ns1_url = 'http://resources.openbel.org/belframework/20150611/namespace/disease-ontology-ids.belns'

ns2 = Path(os.path.join(belns_dir_path, 'mesh-diseases.belns')).as_uri()
ns2_eq = Path(test_eq_2).as_uri()
ns2_url = 'http://resources.openbel.org/belframework/20150611/namespace/mesh-diseases.belns'


class TestDefinitionManagers(FleetingTemporaryCacheMixin):
    @mock_bel_resources
    def test_insert_namespace_persistent(self, mock_get):
        self.manager.ensure_namespace(HGNC_URL)
        help_check_hgnc(self, {HGNC_KEYWORD: self.manager.namespace_cache[HGNC_URL]})

        alternate_manager = CacheManager(connection=self.connection)
        alternate_manager.ensure_namespace(HGNC_URL)
        help_check_hgnc(self, {HGNC_KEYWORD: alternate_manager.namespace_cache[HGNC_URL]})

    @mock_bel_resources
    def test_insert_namespace_nocache(self, mock):
        """Test that this namespace isn't cached"""
        self.assertEqual(0, len(self.manager.list_namespaces()))

        test_ns_nocache_path = 'file:///' + test_ns_nocache
        self.manager.ensure_namespace(test_ns_nocache_path)

        self.assertEqual(0, len(self.manager.list_namespaces()))

    @mock_bel_resources
    def test_insert_annotation(self, mock_get):
        self.manager.ensure_annotation(CELL_LINE_URL)
        self.assertIn(CELL_LINE_URL, self.manager.annotation_cache)
        self.assertIn('1321N1 cell', self.manager.annotation_cache[CELL_LINE_URL])
        self.assertEqual('CLO_0001072', self.manager.annotation_cache[CELL_LINE_URL]['1321N1 cell'])

    @mock_parse_owl_rdf
    @mock_parse_owl_pybel
    def test_insert_owl(self, m1, m2):
        self.manager.ensure_namespace_owl(wine_iri)
        self.assertIn(wine_iri, self.manager.namespace_cache)
        self.assertIn('ChateauMorgon', self.manager.namespace_cache[wine_iri])
        self.assertIn('Winery', self.manager.namespace_cache[wine_iri])


class TestEquivalenceManager(FleetingTemporaryCacheMixin):
    def setUp(self):
        super(TestEquivalenceManager, self).setUp()
        self.manager.drop_equivalences()

    @mock_bel_resources
    def test_make_eq_class(self, mock_get):
        cl = self.manager.ensure_equivalence_class('XXXX')
        self.assertIsInstance(cl, models.NamespaceEntryEquivalence)
        self.assertEqual('XXXX', cl.label)

    @mock_bel_resources
    def test_insert(self, mock_get):
        self.manager.ensure_namespace(ns1)

        ns = self.manager.session.query(models.Namespace).filter_by(url=ns1).one()
        self.assertFalse(ns.has_equivalences)

        self.manager.insert_equivalences(Path(test_eq_1).as_uri(), ns1)

        ns = self.manager.session.query(models.Namespace).filter_by(url=ns1).one()
        self.assertTrue(ns.has_equivalences)

    @mock_bel_resources
    def test_ensure_twice(self, mock_get):
        """No errors should get thrown when ensuring twice"""
        self.manager.ensure_equivalences(ns1_eq, ns1)

    @mock_bel_resources
    def test_disease_equivalence(self, mock_get):
        """Tests that the disease label and ID map to the same equivalence class"""
        alz_eq_class = '0b20937b-5eb4-4c04-8033-63b981decce7'

        self.manager.ensure_equivalences(ns1_eq, ns1)
        x = self.manager.get_equivalence_by_entry(ns1, "Alzheimer's disease")
        self.assertEqual(alz_eq_class, x.label)

        self.manager.ensure_equivalences(ns2_eq, ns2)
        y = self.manager.get_equivalence_by_entry(ns2, "Alzheimer Disease")
        self.assertEqual(alz_eq_class, y.label)

        members = self.manager.get_equivalence_members(alz_eq_class)

        self.assertEqual({
            ns1: "Alzheimer's disease",
            ns2: "Alzheimer Disease"
        }, {member.namespace.url: member.name for member in members})
