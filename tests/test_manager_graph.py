# -*- coding: utf-8 -*-

import os
import tempfile
import unittest

import sqlalchemy.exc

import pybel
from pybel.manager.graph_cache import GraphCacheManager
from tests.constants import BelReconstitutionMixin, test_bel, mock_bel_resources


class TestGraphCache(BelReconstitutionMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = pybel.from_path(test_bel)

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
        path, name, label = test_bel, 'PyBEL Test Document 1', '1.6'

        self.gcm.store_graph(self.g)

        x = self.gcm.ls()

        self.assertEqual(1, len(x))
        self.assertEqual((name, label), x[0])

        g2 = self.gcm.get_graph(name, label)
        self.bel_1_reconstituted(g2)

    @mock_bel_resources
    def test_integrity_failure(self, mock_get):
        """Tests that a graph with the same name and version can't be added twice"""
        self.gcm.store_graph(self.g)

        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.gcm.store_graph(self.g)

    @mock_bel_resources
    def test_get_versions(self, mock_get):
        TEST_V1 = '1.5'
        TEST_V2 = '1.6'

        self.g.document['version'] = TEST_V1
        self.gcm.store_graph(self.g)

        self.g.document['version'] = TEST_V2
        self.gcm.store_graph(self.g)

        self.assertEqual({TEST_V1, TEST_V2}, set(self.gcm.get_graph_versions(self.g.document['name'])))

        self.assertEqual(TEST_V2, self.gcm.get_graph(self.g.document['name']).document['version'])
