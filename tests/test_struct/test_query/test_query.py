# -*- coding: utf-8 -*-

"""Tests for the query builder."""

import logging
import unittest

from pybel import BELGraph, Pipeline
from pybel.dsl import Protein
from pybel.examples.egf_example import egf_graph
from pybel.examples.homology_example import (
    homology_graph, mouse_csf1_protein, mouse_csf1_rna, mouse_mapk1_protein, mouse_mapk1_rna,
)
from pybel.examples.sialic_acid_example import (dap12, shp1, shp2, sialic_acid_graph, syk, trem2, cd33_phosphorylated)
from pybel.struct import expand_nodes_neighborhoods
from pybel.struct import get_subgraph_by_annotation_value
from pybel.struct.mutation import collapse_to_genes, enrich_protein_and_rna_origins
from pybel.struct.query import Query, Seeding
from pybel.testing.generate import generate_random_graph
from pybel.testing.mock_manager import MockQueryManager
from pybel.testing.utils import n

log = logging.getLogger(__name__)


def add(query, manager, graph):
    network = manager.insert_graph(graph)
    query.append_network(network.id)


class TestSeedingConstructor(unittest.TestCase):

    def test_none(self):
        """Test construction of a seeding container."""
        seeding = Seeding()
        self.assertEqual(0, len(seeding))
        self.assertEqual('[]', seeding.dumps())

    def test_append_sample(self):
        seeding = Seeding()
        seeding.append_sample()
        self.assertEqual(1, len(seeding))

        s = seeding.dumps()
        self.assertIsInstance(s, str)


class TestQueryConstructor(unittest.TestCase):
    """Test the construction of a Query."""

    def test_network_ids_none(self):
        query = Query()
        self.assertIsInstance(query.network_ids, list)
        self.assertIsInstance(query.seeding, Seeding)
        self.assertIsInstance(query.pipeline, Pipeline)
        self.assertEqual(0, len(query.network_ids))

    def test_network_ids_single(self):
        query = Query(network_ids=1)
        self.assertIsInstance(query.network_ids, list)
        self.assertEqual(1, len(query.network_ids))

    def test_network_ids_multiple(self):
        query = Query(network_ids=[1, 2, 3])
        self.assertIsInstance(query.network_ids, list)
        self.assertEqual(3, len(query.network_ids))

    def test_network_ids_type_error(self):
        with self.assertRaises(TypeError):
            Query(network_ids='a')

    def test_seeding(self):
        query = Query(seeding=Seeding())
        self.assertEqual(0, len(query.seeding))

    def test_pipeline(self):
        query = Query(pipeline=Pipeline())
        self.assertEqual(0, len(query.pipeline))


class QueryTestEgf(unittest.TestCase):
    """Test querying the EGF subgraph"""

    def setUp(self):
        """Set up each test with a mock query manager."""
        self.manager = MockQueryManager()
        self.query = Query()

    def add_query(self, graph):
        add(self.query, self.manager, graph)
        return self.query

    def run_query(self):
        return self.query.run(self.manager)

    def test_no_seeding_no_pipeline(self):
        graph = egf_graph.copy()

        self.add_query(graph)
        result = self.run_query()

        self.assertEqual(graph.number_of_nodes(), result.number_of_nodes())
        self.assertEqual(graph.number_of_edges(), result.number_of_edges())

    def test_seed_by_neighbor(self):
        graph = BELGraph()
        a, b, c, d = (Protein(namespace=n(), name=str(i)) for i in range(4))

        graph.add_increases(a, b, n(), n())
        graph.add_increases(b, c, n(), n())
        graph.add_increases(c, d, n(), n())

        self.add_query(graph).append_seeding_neighbors(b)
        result = self.run_query()
        self.assertIsInstance(result, BELGraph)
        # test nodes
        self.assertIn(a, result)
        self.assertIn(b, result)
        self.assertIn(c, result)
        self.assertNotIn(d, result)
        # test edges
        self.assertIn(b, result[a])
        self.assertIn(c, result[b])
        self.assertNotIn(d, result[c])

    def test_seed_by_neighbors(self):
        graph = BELGraph()
        a, b, c, d, e = (Protein(namespace=n(), name=str(i)) for i in range(5))

        graph.add_increases(a, b, n(), n())
        graph.add_increases(b, c, n(), n())
        graph.add_increases(c, d, n(), n())
        graph.add_increases(d, e, n(), n())

        self.add_query(graph).append_seeding_neighbors([b, c])

        result = self.run_query()
        self.assertIsInstance(result, BELGraph)
        # test nodes
        self.assertIn(a, result)
        self.assertIn(b, result)
        self.assertIn(c, result)
        self.assertIn(d, result)
        self.assertNotIn(e, result)
        # test edges
        self.assertIn(b, result[a])
        self.assertIn(c, result[b])
        self.assertIn(d, result[c])
        self.assertNotIn(e, result[d])

    def test_random_sample(self):  # TODO this will fail randomly some times lol
        graph = generate_random_graph(50, 1000)

        query = self.add_query(graph)
        query.append_seeding_sample(number_edges=10)
        query.append_seeding_sample(number_edges=10)

        result = self.run_query()

        self.assertEqual(20, result.number_of_edges())


class QueryTest(unittest.TestCase):
    """Test the query"""

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
        test_network = egf_graph.copy()

        enrich_protein_and_rna_origins(test_network)

        network = self.manager.insert_graph(test_network)
        network_id = network.id

        pipeline = Pipeline()
        pipeline.append(get_subgraph_by_annotation_value, 'Annotation', 'foo')

        query = Query(network_ids=[network_id])
        query.append_seeding_neighbors([
            protein_a
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
        query.append_seeding_neighbors([syk])
        query.append_pipeline(enrich_protein_and_rna_origins)

        result = query.run(self.manager)
        self.assertIsNotNone(result, msg='Query returned none')

        self.assertIn(shp1, result)
        self.assertIn(shp2, result)
        self.assertIn(trem2, result)
        self.assertIn(dap12, result)

        self.assertEqual(15, result.number_of_nodes())
        self.assertEqual(14, result.number_of_edges())

    def test_get_subgraph_by_annotation_value(self):
        graph = homology_graph.copy()

        result = get_subgraph_by_annotation_value(graph, 'Species', '10090')
        self.assertIsNotNone(result, msg='Query returned none')
        self.assertIsInstance(result, BELGraph)

        self.assertIn(mouse_mapk1_protein, result, msg='nodes:\n{}'.format(list(map(repr, graph))))
        self.assertIn(mouse_csf1_protein, result)

        self.assertEqual(2, result.number_of_nodes())
        self.assertEqual(1, result.number_of_edges())

    def test_seeding_1(self):
        test_network_1 = self.manager.insert_graph(homology_graph.copy())

        query = Query(network_ids=[test_network_1.id])
        query.append_seeding_neighbors([mouse_csf1_rna, mouse_mapk1_rna])

        result = query.run(self.manager)
        self.assertIsNotNone(result, msg='Query returned none')
        self.assertIsInstance(result, BELGraph)

        self.assertIn(mouse_mapk1_rna, result)
        self.assertIn(mouse_csf1_rna, result)
        self.assertIn(mouse_mapk1_protein, result)
        self.assertIn(mouse_csf1_protein, result)

        self.assertEqual(6, result.number_of_nodes())
        self.assertEqual(4, result.number_of_edges())

    def test_seeding_with_pipeline(self):
        test_network_1 = self.manager.insert_graph(sialic_acid_graph.copy())

        query = Query(network_ids=[test_network_1.id])
        query.append_seeding_neighbors([trem2, dap12, shp2])
        query.append_pipeline(expand_nodes_neighborhoods, [trem2, dap12, shp2])
        result = query.run(self.manager)
        self.assertIsNotNone(result, msg='Query returned none')
        self.assertIsInstance(result, BELGraph)

        self.assertIn(trem2, result)
        self.assertIn(dap12, result)
        self.assertIn(shp2, result)
        self.assertIn(syk, result)
        self.assertIn(cd33_phosphorylated, result)

        self.assertEqual(5, result.number_of_nodes())
        self.assertEqual(4, result.number_of_edges())

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
        self.assertIn(mouse_mapk1_protein, result)
        self.assertIn(mouse_csf1_protein, result)

        self.assertEqual(1, result.number_of_edges())
