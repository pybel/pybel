# -*- coding: utf-8 -*-

"""Tests for the jsonschema node validation."""

import copy
from typing import Any, List, Mapping, Tuple
import unittest

import pymongo
from pymongo.collection import Collection

from pybel import BELGraph, to_nodelink
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
        self.graph = BELGraph()
        self.graph.add_increases(ca, r2, citation=n(), evidence=n())
        self.graph.add_increases(p2, p3, citation=n(), evidence=n())
        self.graph.add_decreases(p3, p1, citation=n(), evidence=n())
        self.links = to_nodelink(self.graph)['links']
        self.collection = to_mongodb(self.graph, TEST_DB.name, TEST_COLLECTION.name)

    def assert_node(self, node: Mapping[str, Any], assert_in=True) -> None:
        """Assert that the given node is present or not present in the MongoDB collection."""
        assert_fn = self.assertEqual
        if not assert_in:
            assert_fn = self.assertNotEqual
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

    def assert_edge(self, edge: dict, assert_in=True) -> None:
        """Assert that the given edge is or isn't present in the Mongo collection."""
        assert_fn = self.assertEqual
        if not assert_in:
            assert_fn = self.assertNotEqual
        if type(edge) is not dict:
            raise ValueError('Expeced type(edge) to be dict. Insead found: ', type(edge))
        # Query the collection for the given edge
        match = self.collection.find_one(edge)
        if match is not None:
            # If a match was found, delete the _id and type keys
            del match['_id'], match['type']
        # Assert that the given edge and match are or are not equal (based on assert_in param)
        assert_fn(edge, match)

    def test_export(self):
        """Test that the to_mongodb export function operates as expeced."""
        # Assert that all nodes in self.graph are in self.collection
        self.assert_node(ca)
        self.assert_node(r2)
        self.assert_node(p2)
        self.assert_node(p3)
        # Assert that the two nodes not in self.graph are not in self.collection
        self.assert_node(g1, assert_in=False)
        self.assert_node(r1, assert_in=False)
        # Assert that every edge from self.graph is in self.collection
        for link in self.links:
            self.assert_edge(link)


if __name__ == '__main__':
    unittest.main()
