# -*- coding: utf-8 -*-

from pybel.examples import sialic_acid_graph
from pybel.examples.sialic_acid_example import cd33, cd33_phosphorylated, shp2, syk, trem2
from pybel.manager.models import Edge, Namespace, Network
from pybel.manager.query_manager import graph_from_edges
from pybel.testing.cases import TemporaryCacheClsMixin
from pybel.testing.mocks import mock_bel_resources

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

        edges = self.manager.query_edges_by_pubmed_identifiers(pmids)

        self.assertLess(0, len(edges))

    def test_seed_by_pmid_no_result(self):
        missing_pmids = ['11111']

        edges = self.manager.query_edges_by_pubmed_identifiers(missing_pmids)

        self.assertEqual(0, len(edges))

    def test_seed_by_induction_raise(self):
        """Test that seeding by induction fails when an empty list is given."""
        with self.assertRaises(ValueError):
            self.manager.query_induction([])

    def test_seed_by_induction_raise_length_one(self):
        """Test that seeding by induction fails when a list of length one is given."""
        shp2_model = self.manager.get_node_by_dict(shp2)

        with self.assertRaises(ValueError):
            self.manager.query_induction([shp2_model])

    def test_seed_by_induction(self):
        """Test seeding by inducing over a list of nodes."""
        shp2_model = self.manager.get_node_by_dict(shp2)
        syk_model = self.manager.get_node_by_dict(syk)
        trem2_model = self.manager.get_node_by_dict(trem2)

        edges = self.manager.query_induction([shp2_model, syk_model, trem2_model])
        self.assertEqual(2, len(edges))

        graph = graph_from_edges(edges)

        self.assertEqual(3, graph.number_of_nodes(), msg='Nodes: {}'.format(graph.nodes()))

        self.assertTrue(graph.has_node_with_data(trem2))
        self.assertTrue(graph.has_node_with_data(syk))
        self.assertTrue(graph.has_node_with_data(shp2))

        self.assertEqual(2, graph.number_of_edges())

    def test_seed_by_neighbors(self):
        """Test seeding a graph by neighbors of a list of nodes."""
        node = self.manager.get_node_by_dict(shp2)
        edges = self.manager.query_neighbors([node])
        self.assertEqual(2, len(edges))

        graph = graph_from_edges(edges)

        self.assertEqual(4, graph.number_of_nodes(), msg='Nodes: {}'.format(graph.nodes()))

        self.assertTrue(graph.has_node_with_data(cd33_phosphorylated))
        self.assertTrue(graph.has_node_with_data(cd33))
        self.assertTrue(graph.has_node_with_data(syk))
        self.assertTrue(graph.has_node_with_data(shp2))

        self.assertEqual(3, graph.number_of_edges())
