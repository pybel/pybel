# -*- coding: utf-8 -*-

import os
from pathlib import Path

from pybel.testing.cases import TemporaryCacheClsMixin
from pybel.testing.constants import belns_dir_path, test_ns_nocache_path
from pybel.testing.mocks import mock_bel_resources
from tests.constants import CELL_LINE_URL, HGNC_URL

ns1 = Path(os.path.join(belns_dir_path, 'disease-ontology.belns')).as_uri()
ns1_url = 'http://resources.openbel.org/belframework/20150611/namespace/disease-ontology-ids.belns'

ns2 = Path(os.path.join(belns_dir_path, 'mesh-diseases.belns')).as_uri()
ns2_url = 'http://resources.openbel.org/belframework/20150611/namespace/mesh-diseases.belns'


class TestDefinitionManagers(TemporaryCacheClsMixin):
    def _help_check_hgnc(self, manager):
        """Help check the HGNC namespace was loaded properly.

        :type manager: pybel.Manager
        """
        entry = manager.get_namespace_entry(HGNC_URL, 'MHS2')
        self.assertIsNotNone(entry)
        self.assertEqual('MHS2', entry.name)
        self.assertIn('G', entry.encoding)

        entry = manager.get_namespace_entry(HGNC_URL, 'MIATNB')
        self.assertIsNotNone(entry)
        self.assertEqual('MIATNB', entry.name)
        self.assertIn('G', entry.encoding)
        self.assertIn('R', entry.encoding)

        entry = manager.get_namespace_entry(HGNC_URL, 'MIA')
        self.assertIsNotNone(entry)
        self.assertEqual('MIA', entry.name)
        self.assertIn('G', entry.encoding)
        self.assertIn('P', entry.encoding)
        self.assertIn('R', entry.encoding)

    @mock_bel_resources
    def test_insert_namespace_persistent(self, mock_get):
        self.assertEqual(0, self.manager.count_namespaces())
        self.assertEqual(0, self.manager.count_namespace_entries())
        self.manager.ensure_namespace(HGNC_URL)
        self._help_check_hgnc(self.manager)

        self.manager.namespace_model.clear()

        self.manager.ensure_namespace(HGNC_URL)
        self._help_check_hgnc(self.manager)

        self.manager.drop_namespace_by_url(HGNC_URL)
        self.assertEqual(0, self.manager.count_namespaces())
        self.assertEqual(0, self.manager.count_namespace_entries())

    def test_insert_namespace_nocache(self):
        """Test that this namespace isn't cached"""
        self.assertEqual(0, self.manager.count_namespaces())
        self.assertEqual(0, self.manager.count_namespace_entries())

        self.manager.ensure_namespace(test_ns_nocache_path)

        self.assertEqual(0, self.manager.count_namespaces())
        self.assertEqual(0, self.manager.count_namespace_entries())

    @mock_bel_resources
    def test_insert_annotation(self, mock_get):
        self.assertEqual(0, self.manager.count_annotations())
        self.assertEqual(0, self.manager.count_annotation_entries())
        annotation = self.manager.ensure_annotation(CELL_LINE_URL)
        self.assertIsNotNone(annotation)
        self.assertEqual(CELL_LINE_URL, annotation.url)

        entry = self.manager.get_annotation_entry(CELL_LINE_URL, '1321N1 cell')
        self.assertEqual('1321N1 cell', entry.name)
        self.assertEqual('CLO_0001072', entry.label)

        self.manager.drop_annotation_by_url(CELL_LINE_URL)
        self.assertEqual(0, self.manager.count_annotations())
        self.assertEqual(0, self.manager.count_annotation_entries())
