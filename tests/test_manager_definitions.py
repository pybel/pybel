# -*- coding: utf-8 -*-

from pybel.manager.cache import CacheManager
from tests.constants import FleetingTemporaryCacheMixin
from tests.constants import HGNC_URL, help_check_hgnc, CELL_LINE_URL, HGNC_KEYWORD
from tests.constants import test_ns_nocache
from tests.constants import wine_iri
from tests.mocks import mock_parse_owl_rdf, mock_bel_resources, mock_parse_owl_pybel


class TestCache(FleetingTemporaryCacheMixin):
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
        self.assertIn(wine_iri, self.manager.namespace_term_cache)
        self.assertIn('ChateauMorgon', self.manager.namespace_term_cache[wine_iri])
        self.assertIn('Winery', self.manager.namespace_term_cache[wine_iri])
