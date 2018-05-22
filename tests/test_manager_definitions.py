# -*- coding: utf-8 -*-

import os
from pathlib import Path

from pybel.manager import Manager
from tests.constants import CELL_LINE_URL, FleetingTemporaryCacheMixin, HGNC_URL, belns_dir_path, test_ns_nocache_path
from tests.mocks import mock_bel_resources

ns1 = Path(os.path.join(belns_dir_path, 'disease-ontology.belns')).as_uri()
ns1_url = 'http://resources.openbel.org/belframework/20150611/namespace/disease-ontology-ids.belns'

ns2 = Path(os.path.join(belns_dir_path, 'mesh-diseases.belns')).as_uri()
ns2_url = 'http://resources.openbel.org/belframework/20150611/namespace/mesh-diseases.belns'


class TestDefinitionManagers(FleetingTemporaryCacheMixin):
    def _help_check_hgnc(self, manager):
        """Helps check the HGNC namespace was loaded properly

        :param Manager manager:
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
        self.manager.ensure_namespace(HGNC_URL)
        self._help_check_hgnc(self.manager)

        alternate_manager = Manager(connection=self.connection)
        alternate_manager.ensure_namespace(HGNC_URL)
        self._help_check_hgnc(alternate_manager)

    def test_insert_namespace_nocache(self):
        """Test that this namespace isn't cached"""
        self.assertEqual(0, len(self.manager.list_namespaces()))
        self.manager.ensure_namespace(test_ns_nocache_path)

        self.assertEqual(0, len(self.manager.list_namespaces()))

    @mock_bel_resources
    def test_insert_annotation(self, mock_get):
        annotation = self.manager.ensure_annotation(CELL_LINE_URL)
        self.assertIsNotNone(annotation)
        self.assertEqual(CELL_LINE_URL, annotation.url)

        entry = self.manager.get_annotation_entry(CELL_LINE_URL, '1321N1 cell')
        self.assertEqual('1321N1 cell', entry.name)
        self.assertEqual('CLO_0001072', entry.label)
