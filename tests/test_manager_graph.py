import os
import tempfile
import unittest

import pybel
from pybel.manager.graph_cache import GraphCacheManager
from tests.constants import test_bel_1, test_bel_3, BelReconstitutionMixin


class TestGraphCache(BelReconstitutionMixin, unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.dir, 'test.db')
        self.connection = 'sqlite:///' + self.db_path
        self.gcm = GraphCacheManager(connection=self.connection)

    def tearDown(self):
        os.remove(self.db_path)
        os.rmdir(self.dir)

    def test_1(self):
        path, name, label = test_bel_1, 'PyBEL Test Document', '1.6'

        g = pybel.from_path(path, complete_origin=True)
        self.gcm.store_graph(g)

        x = self.gcm.ls()

        self.assertEqual(1, len(x))
        self.assertEqual((name, label), x[0])

        g2 = self.gcm.load_graph(name, label)
        self.bel_1_reconstituted(g2)

    def test_get_versions(self):
        g1 = pybel.from_path(test_bel_1)
        g1.graph['document_metadata']['name'] = 'TEST'
        g1.graph['document_metadata']['version'] = '1.6'

        self.gcm.store_graph(g1)

        g2 = pybel.from_path(test_bel_3)
        g2.graph['document_metadata']['name'] = 'TEST'
        g2.graph['document_metadata']['version'] = '1.7'

        self.gcm.store_graph(g2)

        self.assertEqual({'1.7', '1.6'}, set(self.gcm.get_versions('TEST')))

        self.assertEqual('1.7', self.gcm.load_graph('TEST').document['version'])
