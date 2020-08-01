# -*- coding: utf-8 -*-

"""Tests for the jsonschema node validation."""

import copy
from collections import namedtuple
from typing import Any, List, Mapping, Tuple
import unittest

import pymongo
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure

from pybel import BELGraph, to_nodelink
from pybel.dsl import Entity, ComplexAbundance, Gene, Protein, Rna
from pybel.io.mongodb import (
    _entity_to_dict,
    _rm_mongo_keys,
    to_mongodb,
    find_nodes,
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

ca = ComplexAbundance([p1, g2], name='ca', namespace='hgnc')

# Define a namedtuple to make it easier to pass around important node information
NodeInfo = namedtuple('NodeInfo', 'name identifier variants')


class TestMongoDB(unittest.TestCase):
    """Tests for the MongoDB exporting and querying."""
    def setUp(self):
        """Set up MongoDB and create/export a test graph."""
        client = pymongo.MongoClient()
        # Check if there was an error connecting to MongoDB
        try:
            # The ismaster command is cheap and does not require auth.
            client.admin.command('ismaster')
            # Set up the test mongo database and collection
            TEST_DB = client['test_db']
            TEST_COLLECTION = TEST_DB['test_collection']
            TEST_COLLECTION.drop()
            # Create the graph
            self.graph = BELGraph()
            self.graph.add_increases(ca, r2, citation=n(), evidence=n())
            self.graph.add_increases(p2, p3, citation=n(), evidence=n())
            self.graph.add_decreases(p3, p1, citation=n(), evidence=n())
            self.links = to_nodelink(self.graph)['links']
            # Export it to mongo
            self.collection = to_mongodb(self.graph, TEST_DB.name, TEST_COLLECTION.name)

        except ConnectionFailure:
            self.skipTest("Error connecting to a MongoDB server, skipping test.")

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
                _rm_mongo_keys(match)
            # And check that the two nodes are equal
            assert_fn(node_dict, match)

    def assert_edge(self, edge: dict, assert_in=True) -> None:
        """Assert that the given edge is or isn't present in the Mongo collection."""
        assert_fn = self.assertEqual
        if not assert_in:
            assert_fn = self.assertNotEqual
        if not isinstance(edge, dict):
            raise ValueError('Expeced edge to be of type dict. Insead found: ', type(edge))
        # Query the collection for the given edge
        match = self.collection.find_one(edge)
        if match is not None:
            # If a match was found, delete the _id and type keys
            _rm_mongo_keys(match)
        # Assert that the given edge and match are or are not equal (based on assert_in param)
        assert_fn(edge, match)

    def test_export(self):
        """Test that the to_mongodb export function operates as expeced."""
        # Assert that all nodes in self.graph are in self.collection
        for node in self.graph:
            self.assert_node(node)
        # Assert that the two nodes not in self.graph are not in self.collection
        self.assert_node(g1, assert_in=False)
        self.assert_node(r1, assert_in=False)
        # Assert that every edge from self.graph is in self.collection
        for link in self.links:
            self.assert_edge(link)

    def id_info(self, node: dict) -> NodeInfo:
        """Return the important identifying information for a given node."""
        # Get the concept entry (where the name / identifier are stored)
        concept = n['concept']
        name, identifier, variants = None, None, None
        # Query based on name, identifier, variants if they are present
        if 'name' in concept.keys():
            name = concept['name']
        if 'identifier' in concept.keys():
            identifier = concept['identifier']
        if 'variants' in n.keys():
            variants = n['variants']
        return NodeInfo(name=name, identifier=identifier, variants=variants)

    def test_query_nodes(self):
        """Test that the find_nodes() function correctly finds the desired nodes."""
        for node in self.graph:
            n = _entity_to_dict(node)
            # Get the relevant identifying information for the node
            n_info = self.id_info(n)
            # Query the MongoDB based on that info
            matches = find_nodes(
                self.collection, name=n_info.name, identifier=n_info.identifier, variants=n_info.variants
            )
            for match in matches:
                _rm_mongo_keys(match)

            self.assertIn(n, matches)

    def get_true_edges(self, node: dict) -> List[dict]:
        """For a given node, return all its edges from self.links"""
        correct_edges = [edge for edge in self.links
                         if edge['source'] == node or edge['target'] == node]
        return correct_edges

    def test_edges_from_node(self):
        """Test that the get_edges_from_node and _from_criteria functions correctly find all edges for the given node."""
        for node in self.graph:
            # Convert the node to a dict
            n = _entity_to_dict(node)
            # Find all the correct edges pointing to and from the current node
            correct_edges = self.get_true_edges(n)
            # Get the matches from get_edges_from_node()
            matches_from_node = get_edges_from_node(self.collection, n)
            # Get the matches from get_edges_from_criteria()
            criteria = self.id_info(n)
            matches_from_criteria = get_edges_from_criteria(
                self.collection,
                node_name=criteria.name,
                node_identifier=criteria.identifier,
                node_variants=criteria.variants
            )
            # Remove the mongodb-added _id and type keys
            for match1, match2 in zip(matches_from_node, matches_from_criteria):
                _rm_mongo_keys(match1, match2)
            # Assert that the matches_from_node are equal to the correct edges
            self.assertEqual(correct_edges, matches_from_node)
            # Assert that the matches_from_criteria are equal to the correct edges
            self.assertEqual(correct_edges, matches_from_criteria)


if __name__ == '__main__':
    unittest.main()
