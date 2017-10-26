# -*- coding: utf-8 -*-

from pybel.examples import sialic_acid_graph
from pybel.examples.sialic_acid_example import shp2
from pybel.manager.models import Edge, Namespace, Network
from tests.constants import TemporaryCacheClsMixin
from tests.mocks import mock_bel_resources

chebi_url = 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/chebi/chebi-20170725.belns'


class TestSeeding(TemporaryCacheClsMixin):
    """This module tests the seeding functions in the query manager"""

    @classmethod
    def setUpClass(cls):
        """Adds the sialic acid subgraph for all query tests"""
        super(TestSeeding, cls).setUpClass()

        @mock_bel_resources
        def insert(mock):
            """Inserts the Sialic Acid Subgraph using the mock resources"""
            cls.manager.insert_graph(sialic_acid_graph, store_parts=True)

        insert()

    def test_namespace_existence(self):
        a = 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/hgnc-human-genes/hgnc-human-genes-20170725.belns'
        n = self.manager.session.query(Namespace).filter(Namespace.url == a).one()

    def test_namespace_existence_b(self):
        ns = self.manager.session.query(Namespace).filter(Namespace.url == chebi_url).one()
        self.assertIsNotNone(ns)

    def test_sialic_acid_in_node_store(self):
        r = 'sialic acid'

        n = self.manager.get_namespace_entry(chebi_url, r)
        self.assertIsNotNone(n)

        self.assertEqual(r, n.name)

    def test_namespace_existence_c(self):
        a = 'https://arty.scai.fraunhofer.de/artifactory/bel/namespace/go-biological-process/go-biological-process-20170725.belns'
        self.manager.session.query(Namespace).filter(Namespace.url == a).one()

    def test_network_existence(self):
        networks = self.manager.session.query(Network).all()

        self.assertEqual(1, len(networks))

    def test_edge_existence(self):
        edges = self.manager.session.query(Edge).all()

        self.assertEqual(11, len(edges))

    def test_seed_by_pmid(self):
        pmids = ['26438529']

        edges = self.manager.query_edges_by_pmid(pmids)

        self.assertLess(0, len(edges))

    def test_seed_by_pmid_no_result(self):
        missing_pmids = ['11111']

        edges = self.manager.query_edges_by_pmid(missing_pmids)

        self.assertEqual(0, len(edges))

    def test_seed_by_neighbors(self):
        node = self.manager.get_node_by_dict(shp2)
        edges = self.manager.query_neighbors([node])
        self.assertEqual(2, len(edges))
