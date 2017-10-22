# -*- coding: utf-8 -*-

from pybel.examples import sialic_acid_graph
from pybel.examples.sialic_acid_example import shp2
from tests.constants import TemporaryCacheClsMixin
from tests.mocks import mock_bel_resources


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
