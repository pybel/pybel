# -*- coding: utf-8 -*-

"""Tests for the jsonschema node validation."""

import copy
from typing import Any, List, Mapping, Tuple
import unittest

import pymongo
from pymongo.collection import Collection

from pybel import BELGraph
from pybel.dsl import Entity, ComplexAbundance, Gene, Protein, Rna
from pybel.io.mongodb import (
    _entity_to_dict, to_mongodb,
    get_edges_from_node,
    get_edges_from_criteria
)
from pybel.testing.utils import n

g1 = Gene('hgnc', '1')
r1 = Rna('hgnc', '1')
p1 = Protein('hgnc', '1')
g2 = Gene('hgnc', '2')
r2 = Rna('hgnc', '2')
p2 = Protein('hgnc', '2')
g3 = Gene('hgnc', '3')
p3 = Protein('hgnc', '3')

ca = ComplexAbundance([p1, g2], name='ca')

client = pymongo.MongoClient()
TEST_DB = client['test_db']
TEST_COLLECTION = TEST_DB['test_collection']
TEST_COLLECTION.drop()


class TestMongoDB(unittest.TestCase):
    """Tests for the MongoDB exporting and querying."""
    def setUp(self):
        """Create and export a test graph."""
        graph = BELGraph()
        graph.add_increases(ca, r2, citation=n(), evidence=n())
        graph.add_increases(p2, p3, citation=n(), evidence=n())
        graph.add_decreases(p3, p1, citation=n(), evidence=n())
        self.collection = to_mongodb(graph, TEST_DB.name, TEST_COLLECTION.name)

    def _assert_node(self, node: Mapping[str, Any], assert_fn) -> None:
        """Assert that the given node is present or not present in the MongoDB collection."""
        # Convert the node to a dict so it can be matched against entries in the MongoDB
        node_dict = _entity_to_dict(node)
        match = self.collection.find_one(node_dict)
        # If the passed node has a MongoDB unique _id, check that the two ids match
        if '_id' in node.keys():
            assert_fn(node_dict['_id'], match['_id'])
        else:
            # Otherwise, delete the parameters type and _id unique to the to_mongodb output
            if match is not None:
                del match['_id'], match['type']
            # And check that the two nodes are equal
            assert_fn(node_dict, match)

    def assert_node_in(self, node: Mapping[str, Any]) -> None:
        """Assert that the given node is present in the MongoDB collection."""
        self._assert_node(node, self.assertEqual)

    def assert_node_not_in(self, node: Mapping[str, Any]) -> None:
        """Assert that the given node is present in the MongoDB collection."""
        self._assert_node(node, self.assertNotEqual)

    def test_export(self):
        """Test that the to_mongodb export function operates as expeced."""
        self.assert_node_in(ca)
        self.assert_node_in(r2)
        self.assert_node_in(p2)
        self.assert_node_in(p3)

        self.assert_node_not_in(g1)
        self.assert_node_not_in(r1)


if __name__ == '__main__':
    unittest.main()
