# -*- coding: utf-8 -*-

import os
import tempfile
import unittest

import sqlalchemy.exc

import pybel
from pybel.constants import METADATA_NAME, METADATA_VERSION
from pybel.manager.graph_cache import GraphCacheManager
from tests.constants import BelReconstitutionMixin, test_bel_thorough, mock_bel_resources, \
    expected_test_thorough_metadata


class TestGraphCache(BelReconstitutionMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = pybel.from_path(test_bel_thorough, allow_nested=True)

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.dir, 'test.db')
        self.connection = 'sqlite:///' + self.db_path
        self.gcm = GraphCacheManager(connection=self.connection)

    def tearDown(self):
        os.remove(self.db_path)
        os.rmdir(self.dir)

    @mock_bel_resources
    def test_load_reload(self, mock_get):
        name = expected_test_thorough_metadata[METADATA_NAME]
        version = expected_test_thorough_metadata[METADATA_VERSION]

        self.gcm.insert_graph(self.graph)

        x = self.gcm.ls()

        self.assertEqual(1, len(x))
        self.assertEqual((1, name, version), x[0])

        g2 = self.gcm.get_graph(name, version)
        self.bel_thorough_reconstituted(g2)

    @mock_bel_resources
    def test_integrity_failure(self, mock_get):
        """Tests that a graph with the same name and version can't be added twice"""
        self.gcm.insert_graph(self.graph)

        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.gcm.insert_graph(self.graph)

    @mock_bel_resources
    def test_get_versions(self, mock_get):
        TEST_V1 = '0.9'
        TEST_V2 = expected_test_thorough_metadata[METADATA_VERSION]  # Actually is 1.0

        self.graph.document[METADATA_VERSION] = TEST_V1
        self.gcm.insert_graph(self.graph)

        self.graph.document[METADATA_VERSION] = TEST_V2
        self.gcm.insert_graph(self.graph)

        self.assertEqual({TEST_V1, TEST_V2}, set(self.gcm.get_graph_versions(self.graph.document[METADATA_NAME])))

        self.assertEqual(TEST_V2, self.gcm.get_graph(self.graph.document[METADATA_NAME]).document[METADATA_VERSION])
