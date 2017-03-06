# -*- coding: utf-8 -*-

import os
import tempfile
import unittest
from collections import Counter

import sqlalchemy.exc

import pybel
from pybel.constants import METADATA_NAME, METADATA_VERSION
from pybel.manager import models
from pybel.manager.graph_cache import GraphCacheManager
from tests import constants
from tests.constants import BelReconstitutionMixin, test_bel_thorough, mock_bel_resources, \
    expected_test_thorough_metadata, test_bel_simple

TEST_BEL_NAME = 'PyBEL Test Document 1'
TEST_BEL_VERSION = '1.6'


class TestGraphCache(BelReconstitutionMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = pybel.from_path(test_bel_thorough, allow_nested=True)
        cls.simple_graph = pybel.from_path(test_bel_simple)

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

    @mock_bel_resources
    def test_get_or_create_node(self, mock_get):
        network = self.gcm.insert_graph(self.simple_graph, store_parts=True)

        citations = self.gcm.session.query(models.Citation).all()
        self.assertEqual(2, len(citations))

        citations_strs = {'123455', '123456'}
        self.assertEqual(citations_strs, {e.reference for e in citations})

        authors = {'Example Author', 'Example Author2'}
        self.assertEqual(authors, {a.name for a in self.gcm.session.query(models.Author).all()})

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
        self.bel_simple_reconstituted(g2)


@unittest.skip('Feature not started yet')
class TestFilter(BelReconstitutionMixin, unittest.TestCase):
    """Tests that a graph can be reconstructed from the edge and node relational tables in the database

    1. Load graph (test BEL 1 or test thorough)
    2. Add sentinel annotation to ALL edges
    3. Store graph
    4. Query for all edges with sentinel annotation
    5. Compare to original graph
    """

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.dir, 'test.db')
        self.connection = 'sqlite:///' + self.db_path
        self.gcm = GraphCacheManager(connection=self.connection)
        self.graph = pybel.from_path(test_bel_thorough, allow_nested=True)

    @mock_bel_resources
    def test_database_edge_filter(self, mock_get):
        self.help_database_edge_filter(test_bel_simple, self.bel_simple_reconstituted)

    @mock_bel_resources
    def test_database_edge_filter(self, mock_get):
        self.help_database_edge_filter(test_bel_thorough, self.bel_thorough_reconstituted)

    def help_database_edge_filter(self, path, compare, annotation_tag='MeSHDisease', value_tag='Arm Injuries'):
        """Helps to test the graph that is created by a specific annotation.

        :param path: Path to the test BEL file.
        :type path: str
        :param compare: Method that should be used to compare the original and resulting graph.
        :type compare:
        :param annotation_tag: Annotation that marks the nodes with an annotation.
        :type annotation_tag: str
        :param value_tag: Annotation value for the given sentinel_annotation.
        :type value_tag: str
        """

        original = pybel.from_path(path)

        compare(original)

        for u, v, k in original.edges(keys=True):
            original.edge[u][v][k][annotation_tag] = value_tag

        self.gcm.insert_graph(original, store_parts=True)

        reloaded = self.gcm.get_by_edge_filter(**{annotation_tag: value_tag})

        for u, v, k in reloaded.edges(keys=True):
            del reloaded.edge[u][v][k][annotation_tag]

        compare(reloaded, check_metadata=False)
