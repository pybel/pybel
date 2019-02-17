# -*- coding: utf-8 -*-

from pybel.constants import hbp_namespace
from pybel.examples import sialic_acid_graph
from pybel.examples.sialic_acid_example import cd33, cd33_phosphorylated, shp2, syk, trem2
from pybel.manager.models import Edge, Namespace, Network
from pybel.manager.query_manager import graph_from_edges
from pybel.testing.cases import TemporaryCacheClsMixin
from pybel.testing.mocks import mock_bel_resources


class TestSeeding(TemporaryCacheClsMixin):
    """This module tests the seeding functions in the query manager."""

    @classmethod
    def setUpClass(cls):
        """Add the Sialic Acid subgraph for all query tests."""
        super().setUpClass()

        with mock_bel_resources:
            cls.manager.insert_graph(sialic_acid_graph, store_parts=True)

    def test_namespace_existence(self):
        """Check the sialic acid graph has the right namespaces, and they're uploaded properly."""
        ns = self.manager.session.query(Namespace).filter(Namespace.url == hbp_namespace('hgnc')).one()
        self.assertIsNotNone(ns)

        ns = self.manager.session.query(Namespace).filter(Namespace.url == hbp_namespace('chebi')).one()
        self.assertIsNotNone(ns)

        ns = self.manager.session.query(Namespace).filter(Namespace.url == hbp_namespace('go')).one()
        self.assertIsNotNone(ns)

    def test_sialic_acid_in_node_store(self):
        r = 'sialic acid'

        n = self.manager.get_namespace_entry(hbp_namespace('chebi'), r)
        self.assertIsNotNone(n)

        self.assertEqual(r, n.name)

    def test_network_existence(self):
        networks = self.manager.session.query(Network).all()

        self.assertEqual(1, len(networks))

    def test_edge_existence(self):
        edges = self.manager.session.query(Edge).all()

        self.assertEqual(11, len(edges))

    def test_seed_by_pmid(self):
        pmids = ['26438529']
        edges = self.manager.query_edges_by_pubmed_identifiers(pmids)
        self.assertLessEqual(1, len(edges))

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
        shp2_model = self.manager.get_node_by_dsl(shp2)

        with self.assertRaises(ValueError):
            self.manager.query_induction([shp2_model])

    def test_seed_by_induction(self):
        """Test seeding by inducing over a list of nodes."""
        shp2_model = self.manager.get_node_by_dsl(shp2)
        self.assertIsNotNone(shp2_model)
        syk_model = self.manager.get_node_by_dsl(syk)
        self.assertIsNotNone(syk_model)
        trem2_model = self.manager.get_node_by_dsl(trem2)
        self.assertIsNotNone(trem2_model)

        edges = self.manager.query_induction([shp2_model, syk_model, trem2_model])
        self.assertEqual(2, len(edges))

        graph = graph_from_edges(edges)

        self.assertEqual(3, graph.number_of_nodes())

        self.assertIn(trem2, graph)
        self.assertIn(syk, graph)
        self.assertIn(shp2, graph)

        self.assertEqual(3, graph.number_of_nodes())
        self.assertEqual(2, graph.number_of_edges())

    def test_seed_by_neighbors(self):
        """Test seeding a graph by neighbors of a list of nodes."""
        shp2_model = self.manager.get_node_by_dsl(shp2)
        self.assertIsNotNone(shp2_model)

        edges = self.manager.query_neighbors([shp2_model])
        self.assertEqual(2, len(edges))

        graph = graph_from_edges(edges)
        self.assertEqual(3, graph.number_of_edges())

        self.assertEqual(4, graph.number_of_nodes())

        self.assertIn(cd33_phosphorylated, graph)
        self.assertIn(cd33, graph)
        self.assertIn(syk, graph)
        self.assertIn(shp2, graph)

        self.assertEqual(3, graph.number_of_edges())
