import unittest

import pybel
from pybel.manager.graph_cache import GraphCacheManager
from tests.constants import test_bel_1, bel_1_reconstituted


class TestGraphCache(unittest.TestCase):
    def setUp(self):
        self.gcm = GraphCacheManager('sqlite://')

    def test_1(self):
        path, name, label = test_bel_1, 'PyBEL Test Document', '1.6'

        g = pybel.from_path(path, complete_origin=True)
        self.gcm.store_graph(g)

        x = self.gcm.ls()

        self.assertEqual(1, len(x))
        self.assertEqual((name, label), x[0])

        g2 = self.gcm.load_graph(name, label)
        bel_1_reconstituted(self, g2)
