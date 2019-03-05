# -*- coding: utf-8 -*-

import os
from pathlib import Path

from pybel import BELGraph
from pybel.constants import ANNOTATIONS, OPENBEL_ANNOTATION_RESOURCES
from pybel.testing.cases import TemporaryCacheClsMixin
from pybel.testing.constants import belns_dir_path, test_ns_nocache_path
from pybel.testing.mocks import mock_bel_resources
from tests.constants import HGNC_URL

ns1 = Path(os.path.join(belns_dir_path, 'disease-ontology.belns')).as_uri()
ns1_url = 'http://resources.openbel.org/belframework/20150611/namespace/disease-ontology-ids.belns'

ns2 = Path(os.path.join(belns_dir_path, 'mesh-diseases.belns')).as_uri()
ns2_url = 'http://resources.openbel.org/belframework/20150611/namespace/mesh-diseases.belns'

CELL_LINE_URL = OPENBEL_ANNOTATION_RESOURCES + 'cell-line.belanno'
CELL_LINE_KEYWORD = 'CellLine'


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
        self.manager.get_or_create_namespace(HGNC_URL)
        self._help_check_hgnc(self.manager)

        self.manager.get_or_create_namespace(HGNC_URL)
        self._help_check_hgnc(self.manager)

        self.manager.drop_namespace_by_url(HGNC_URL)
        self.assertEqual(0, self.manager.count_namespaces())
        self.assertEqual(0, self.manager.count_namespace_entries())

    def test_insert_namespace_nocache(self):
        """Test that this namespace isn't cached"""
        self.assertEqual(0, self.manager.count_namespaces())
        self.assertEqual(0, self.manager.count_namespace_entries())

        self.manager.get_or_create_namespace(test_ns_nocache_path)

        self.assertEqual(0, self.manager.count_namespaces())
        self.assertEqual(0, self.manager.count_namespace_entries())

    @mock_bel_resources
    def test_insert_annotation(self, mock_get):
        self.assertEqual(0, self.manager.count_annotations())
        self.assertEqual(0, self.manager.count_annotation_entries())
        annotation = self.manager.get_or_create_annotation(CELL_LINE_URL)
        self.assertIsNotNone(annotation)
        self.assertEqual(CELL_LINE_URL, annotation.url)

        entry = self.manager.get_namespace_entry(CELL_LINE_URL, '1321N1 cell')
        self.assertEqual('1321N1 cell', entry.name)
        self.assertEqual('CLO_0001072', entry.identifier)

        entries = self.manager.get_annotation_entries_by_names(CELL_LINE_URL, ['1321N1 cell'])
        self.assertIsNotNone(entries)
        self.assertEqual(1, len(entries))
        entry = entries[0]
        self.assertEqual('1321N1 cell', entry.name)
        self.assertEqual('CLO_0001072', entry.identifier)

        graph = BELGraph()
        graph.annotation_url[CELL_LINE_KEYWORD] = CELL_LINE_URL

        data = {
            ANNOTATIONS: {
                CELL_LINE_KEYWORD: {
                    '1321N1 cell': True
                }
            }
        }

        annotations_iter = dict(self.manager._iter_from_annotations_dict(graph, annotations_dict=data[ANNOTATIONS]))
        self.assertIn(CELL_LINE_URL, annotations_iter)
        self.assertIn('1321N1 cell', annotations_iter[CELL_LINE_URL])

        entries = self.manager._get_annotation_entries_from_data(graph, data)
        self.assertIsNotNone(entries)
        self.assertEqual(1, len(entries))
        entry = entries[0]
        self.assertEqual('1321N1 cell', entry.name)
        self.assertEqual('CLO_0001072', entry.identifier)

        self.manager.drop_namespace_by_url(CELL_LINE_URL)
        self.assertEqual(0, self.manager.count_annotations())
        self.assertEqual(0, self.manager.count_annotation_entries())

    def test_get_annotation_entries_no_data(self):
        """Test that if there's no ANNOTATIONS entry in the data, it just returns none."""
        graph = BELGraph()
        data = {}
        entries = self.manager._get_annotation_entries_from_data(graph, data)
        self.assertIsNone(entries)
