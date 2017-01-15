import os
import tempfile
import unittest
from collections import Counter

import sqlalchemy.exc

import pybel
from pybel.manager import models
from pybel.manager.graph_cache import GraphCacheManager
from tests import constants
from tests.constants import BelReconstitutionMixin, test_bel, mock_bel_resources

TEST_BEL_NAME = 'PyBEL Test Document 1'
TEST_BEL_VERSION = '1.6'

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
        self.gcm.store_graph(self.g)

        x = self.gcm.ls()

        self.assertEqual(1, len(x))
        self.assertEqual((TEST_BEL_NAME, TEST_BEL_VERSION), x[0])

        g2 = self.gcm.get_graph(TEST_BEL_NAME, TEST_BEL_VERSION)
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

    @mock_bel_resources
    def test_get_or_create_node(self, mock_get):
        network = self.gcm.store_graph(self.g, store_parts=True)

        citations = self.gcm.session.query(models.Citation).all()
        self.assertEqual(2, len(citations))

        citations_strs = {'123455', '123456'}
        self.assertEqual(citations_strs, {e.reference for e in citations})

        evidences = self.gcm.session.query(models.Evidence).all()
        self.assertEqual(3, len(evidences))

        evidences_strs = {'Evidence 1 w extra notes', 'Evidence 2', 'Evidence 3'}
        self.assertEqual(evidences_strs, {e.text for e in evidences})

        nodes = self.gcm.session.query(models.Node).all()
        self.assertEqual(4, len(nodes))

        edges = self.gcm.session.query(models.Edge).all()

        x = Counter((e.source.bel, e.target.bel) for e in edges)

        pfmt = 'p(HGNC:{})'
        d = {
            (pfmt.format(constants.AKT1[2]), pfmt.format(constants.EGFR[2])): 1,
            (pfmt.format(constants.EGFR[2]), pfmt.format(constants.FADD[2])): 1,
            (pfmt.format(constants.EGFR[2]), pfmt.format(constants.CASP8[2])): 1,
            (pfmt.format(constants.FADD[2]), pfmt.format(constants.CASP8[2])): 1,
            (pfmt.format(constants.AKT1[2]), pfmt.format(constants.CASP8[2])): 1,  # two way association
            (pfmt.format(constants.CASP8[2]), pfmt.format(constants.AKT1[2])): 1  # two way association
        }

        self.assertEqual(dict(x), d)

        network_edge_associations = self.gcm.session.query(models.network_edge).filter_by(network_id=network.id).all()
        self.assertEqual({nea.edge_id for nea in network_edge_associations},
                         {edge.id for edge in edges})

        g2 = self.gcm.get_graph(TEST_BEL_NAME, TEST_BEL_VERSION)
        self.bel_1_reconstituted(g2)
