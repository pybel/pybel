# -*- coding: utf-8 -*-

"""Tests for the jsonschema node validation."""

from copy import deepcopy
from collections import namedtuple
from typing import Any, List, Mapping, Optional, Tuple
import unittest

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure

from pybel import BELGraph, to_sbel, BaseEntity
from pybel.constants import (
    COMPLEX, COMPOSITE, CONCEPT, FUNCTION, IDENTIFIER,
    MEMBERS, NAME, SOURCE, TARGET, VARIANTS,
)
from pybel.dsl import Entity, ComplexAbundance, Gene, Protein, Rna
from pybel.io.mongodb import (
    _rm_mongo_keys,
    to_mongodb,
    find_nodes,
    get_edges_from_node,
    get_edges_from_criteria
)
from pybel.testing.utils import n as n_

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
NodeInfo = namedtuple('NodeInfo', 'name identifier function variants')


def id_info(node: Mapping[str, Any]) -> NodeInfo:
    """Return the important identifying information for a given node."""
    # Get the concept entry (where the name / identifier are stored)
    concept = node[CONCEPT]
    # Get the id info
    name = concept.get(NAME)
    identifier = concept.get(IDENTIFIER)

    function = node.get(FUNCTION)
    variants = node.get(VARIANTS)

    return NodeInfo(name=name, identifier=identifier, function=function, variants=variants)


def _entity_to_dict(entity: Entity) -> Mapping[str, Any]:
    """Input a pybel Entity and return a dict representing it."""
    new_node = dict(entity)
    if new_node[FUNCTION] in [COMPLEX, COMPOSITE]:
        new_node[MEMBERS] = list(map(dict, new_node[MEMBERS]))
    return new_node


def _edge_to_dict(edge: Mapping[str, Any]) -> dict:
    """Helper function to convert an edge to a dictionary."""
    new_edge = dict(deepcopy(edge))
    for key in (SOURCE, TARGET):
        new_edge[key] = _entity_to_dict(new_edge[key])
    return new_edge


def _clean_entity(entity):
    """Remove the 'bel' and 'id' properties from an entity"""
    for prop in ('bel', 'id'):
        if entity.get(prop):
            del entity[prop]


class TestMongoDB(unittest.TestCase):
    """Tests for the MongoDB exporting and querying."""
    def setUp(self):
        """Set up MongoDB and create/export a test graph."""
        client = MongoClient()
        # Check if there was an error connecting to MongoDB
        try:
            # The ismaster command is cheap and does not require auth.
            # If it fails, there was a connection failure
            client.admin.command('ismaster')
            # Set up the test mongo database and collection
            TEST_DB = client['test_db']
            TEST_COLLECTION = TEST_DB['test_collection']
            TEST_COLLECTION.drop()
            # Create the graph
            self.graph = BELGraph()
            self.graph.add_increases(ca, r2, citation=n_(), evidence=n_())
            self.graph.add_increases(p2, p3, citation=n_(), evidence=n_())
            self.graph.add_decreases(p3, p1, citation=n_(), evidence=n_())
            # Store the links separately
            self.links = to_sbel(self.graph, yield_metadata=False)
            # Export the graph to mongo
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
        # Delete the parameters type and _id unique to the to_mongodb output
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
            raise ValueError('Expected edge to be of type dict. Insead found: ', type(edge))
        # Convert the edge child elements (source, target) to dicts
        edge = _edge_to_dict(edge)
        # Query the collection for the given edge
        match = self.collection.find_one(edge)
        if match is not None:
            # If a match was found, delete the _id and type keys
            _rm_mongo_keys(match)
        # Assert that the given edge and match are or are not equal (based on assert_in param)
        assert_fn(edge, match)

    def test_export(self):
        """Test that the to_mongodb export function operates as expected."""
        # Assert that all nodes in self.graph are in self.collection
        for node in self.graph:
            self.assert_node(node)
        # Assert that the two nodes not in self.graph are not in self.collection
        self.assert_node(g1, assert_in=False)
        self.assert_node(r1, assert_in=False)
        # Assert that every edge from self.graph is in self.collection
        for link in self.links:
            self.assert_edge(link)

    def test_query_nodes(self):
        """Test that the find_nodes() function correctly finds the desired nodes."""
        for node in self.graph:
            # Get the relevant identifying information for the node
            n_info = id_info(node)
            # Query the MongoDB based on that info
            matches = find_nodes(
                self.collection,
                name=n_info.name,
                identifier=n_info.identifier,
                function=n_info.function,
                variants=n_info.variants
            )
            for match in matches:
                self.assertIsInstance(match, BaseEntity)
            for match in matches:
                _rm_mongo_keys(match)

            self.assertIn(node, matches)

    def _get_true_edges(self, node: Mapping[str, Any]) -> List[dict]:
        """For a given node, return all its edges from self.links"""
        n = _entity_to_dict(node)
        _clean_entity(n)
        correct_edges: List[dict] = []
        for edge in self.links:
            # Convert the edge to a dict for comparison
            dict_edge = _edge_to_dict(edge)
            # Create a copy of dict_edge so properties can be deleted
            comparison_edge = deepcopy(dict_edge)
            # Remove the 'bel' and 'id' properties from the edge's source and target
            for node_name in (SOURCE, TARGET):
                _clean_entity(comparison_edge[node_name])
            # Check whether node n is the source or target of the edge
            if n in (comparison_edge[SOURCE], comparison_edge[TARGET]):
                correct_edges.append(dict_edge)
        return correct_edges

    def _edges_from_node(self, node: Mapping[str, Any]) -> List[dict]:
        """Return the matching edges for the given node from get_edges_from_node()."""
        # Get the matches from get_edges_from_node()
        matches_from_node = get_edges_from_node(self.collection, node)
        # Remove the mongodb-added _id and type keys
        for match in matches_from_node:
            _rm_mongo_keys(match)
        return matches_from_node

    def _edges_from_criteria(self, node: Mapping[str, Any]) -> List[dict]:
        """Return the matching edges for the given node from get_edges_from_node()."""
        # Get the matches from get_edges_from_criteria()
        criteria = id_info(node)
        pairs_from_criteria = get_edges_from_criteria(
            self.collection,
            node_name=criteria.name,
            node_identifier=criteria.identifier,
            node_function=criteria.function,
            node_variants=criteria.variants
        )
        matches_from_criteria = []
        # Since get_edges_from_criteria can return edges for multiple matching nodes,
        # loop through every tuple (node, [edges...]) in pairs_from_criteria
        for node_match, edges_match in pairs_from_criteria.items():
            # If node_match is equal to the given node, let matches_from_criteria equal the returned edges
            if node_match == node:
                matches_from_criteria = edges_match
                break
        # Remove the mongo keys from each match
        for match in matches_from_criteria:
            _rm_mongo_keys(match)
        return matches_from_criteria

    def test_get_edges(self):
        """Test that the get_edges_from_node and _from_criteria functions correctly find all edges for the given node."""
        for node in self.graph:
            # Find all the correct edges pointing to and from the current node
            correct_edges = self._get_true_edges(node)

            # Get the matching edges from get_edges_from_node()
            matches_from_node = self._edges_from_node(node)
            # Get the matching edges from get_edges_from_criteria()
            matches_from_criteria = self._edges_from_criteria(node)

            # Assert that the matches_from_node are equal to the correct edges
            self.assertEqual(correct_edges, matches_from_node)
            # Assert that the matches_from_criteria are equal to the correct edges
            self.assertEqual(correct_edges, matches_from_criteria)


if __name__ == '__main__':
    unittest.main()
