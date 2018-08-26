# -*- coding: utf-8 -*-

"""Tests for the query builder."""

import logging
import unittest

from pybel import BELGraph, Pipeline
from pybel.examples import egf_graph
from pybel.examples.homology_example import (
    homology_graph, mouse_csf1_protein, mouse_csf1_rna, mouse_mapk1_protein, mouse_mapk1_rna,
)
from pybel.examples.sialic_acid_example import dap12, shp1, shp2, sialic_acid_graph, syk, trem2
from pybel.struct import get_subgraph_by_annotation_value
from pybel.struct.mutation import collapse_to_genes, enrich_protein_and_rna_origins
from pybel.struct.query import Query
from tests.test_struct.test_query.mocks import MockQueryManager

log = logging.getLogger(__name__)


class TestMockManager(unittest.TestCase):
    """Tests for the mock query manager."""

    def test_make(self):
        """Test instantiating the mock query manager."""
        manager = MockQueryManager()
        self.assertEqual(0, manager.count_networks())

    def test_make_with_graph(self):
        """Test counting networks in the mock query manager."""
        manager = MockQueryManager(graphs=[egf_graph])
        self.assertEqual(1, manager.count_networks())


class QueryTest(unittest.TestCase):
    def setUp(self):
        """Setup each test with an empty mock query manager."""
        self.manager = MockQueryManager()

    def test_pipeline(self):
        test_graph_1 = egf_graph.copy()
        enrich_protein_and_rna_origins(test_graph_1)

        self.assertEqual(9, test_graph_1.number_of_nodes())  # 4 nodes already there +  2*2 proteins + 1 (rna)
        self.assertEqual(8, test_graph_1.number_of_edges())  # 3 already there + 2*2 proteins + 1 (rna)

        network = self.manager.insert_graph(test_graph_1)

        pipeline = Pipeline()
        pipeline.append(collapse_to_genes)

        query = Query(
            network_ids=[network.id],
            pipeline=pipeline
        )
        result_graph = query.run(self.manager)

        self.assertEqual(4, result_graph.number_of_nodes())  # same number of nodes than there were
        self.assertEqual(3, result_graph.number_of_edges())  # same number of edges than there were

    def test_pipeline_2(self):
        test_network = self.graph_1  # Defined in test.constants.TestNetworks

        enrich_protein_and_rna_origins(test_network)

        network = self.manager.insert_graph(test_network)
        network_id = network.id

        pipeline = Pipeline()
        pipeline.append(get_subgraph_by_annotation_value, 'Annotation', 'foo')

        query = Query(network_ids=[network_id])
        query.append_seeding_neighbors([
            protein_a_tuple
        ])
        query.pipeline = pipeline

        result = query.run(self.manager, in_place=False)
        self.assertIsNotNone(result, msg='Query returned none')

        self.assertEqual(3, result.number_of_nodes())  # only expanded to node protein_a and gene_c
        self.assertEqual(2, result.number_of_edges())  # three nodes with two relationships

    def test_query_multiple_networks(self):
        egf_network = self.manager.insert_graph(sialic_acid_graph.copy())
        sialic_acid_network = self.manager.insert_graph(egf_graph.copy())

        query = Query()
        query.append_network(egf_network.id)
        query.append_network(sialic_acid_network.id)
        query.append_seeding_neighbors([syk.as_tuple()])
        query.append_pipeline(enrich_protein_and_rna_origins)

        result = query.run(self.manager, in_place=False)
        self.assertIsNotNone(result, msg='Query returned none')

        self.assertIn(shp1.as_tuple(), result)
        self.assertIn(shp2.as_tuple(), result)
        self.assertIn(trem2.as_tuple(), result)
        self.assertIn(dap12.as_tuple(), result)

        self.assertEqual(15, result.number_of_nodes())
        self.assertEqual(14, result.number_of_edges())

    def test_get_subgraph_by_annotation_value(self):
        graph = homology_graph.copy()

        result = get_subgraph_by_annotation_value(graph, 'Species', '10090')
        self.assertIsNotNone(result, msg='Query returned none')
        self.assertIsInstance(result, BELGraph)

        self.assertIn(mouse_mapk1_protein.as_tuple(), result)
        self.assertIn(mouse_csf1_protein.as_tuple(), result)

        self.assertEqual(2, result.number_of_nodes())
        self.assertEqual(1, result.number_of_edges())

    def test_seeding_1(self):
        test_network_1 = self.manager.insert_graph(homology_graph.copy())

        query = Query(network_ids=[test_network_1.id])
        query.append_seeding_neighbors([mouse_csf1_rna, mouse_mapk1_rna])

        result = query.run(self.manager, in_place=False)
        self.assertIsNotNone(result, msg='Query returned none')
        self.assertIsInstance(result, BELGraph)

        self.assertIn(mouse_mapk1_rna.as_tuple(), result)
        self.assertIn(mouse_csf1_rna.as_tuple(), result)
        self.assertIn(mouse_mapk1_protein.as_tuple(), result)
        self.assertIn(mouse_csf1_protein.as_tuple(), result)

        self.assertEqual(6, result.number_of_nodes())
        self.assertEqual(4, result.number_of_edges())

    def test_seeding_with_pipeline(self):
        test_network_1 = self.manager.insert_graph(homology_graph.copy())

        query = Query(network_ids=[test_network_1.id])
        query.append_seeding_neighbors([mouse_csf1_rna, mouse_mapk1_rna])
        query.append_pipeline(expand_internal)
        result = query.run(self.manager, in_place=False)
        self.assertIsNotNone(result, msg='Query returned none')
        self.assertIsInstance(result, BELGraph)

        self.assertIn(mouse_mapk1_rna.as_tuple(), result)
        self.assertIn(mouse_csf1_rna.as_tuple(), result)
        self.assertIn(mouse_mapk1_protein.as_tuple(), result)
        self.assertIn(mouse_csf1_protein.as_tuple(), result)

        self.assertEqual(6, result.number_of_nodes())
        self.assertEqual(5, result.number_of_edges())

    def test_query_multiple_networks_with_api(self):
        test_network_1 = self.manager.insert_graph(homology_graph.copy())

        pipeline = Pipeline()
        pipeline.append(get_subgraph_by_annotation_value, 'Species', '10090')

        query = Query(
            network_ids=[test_network_1.id],
            pipeline=pipeline
        )
        query.append_seeding_neighbors([mouse_csf1_rna, mouse_mapk1_rna])

        result = query.run(self.manager, in_place=False)
        self.assertIsNotNone(result, msg='Query returned none')

        self.assertEqual(2, result.number_of_nodes())
        self.assertIn(mouse_mapk1_protein.as_tuple(), result)
        self.assertIn(mouse_csf1_protein.as_tuple(), result)

        self.assertEqual(1, result.number_of_edges())
