# -*- coding: utf-8 -*-
"""An exporter from PyBEL graphs to a local Mongo database."""

import copy
from typing import Any, List, Mapping, Tuple

import pybel
from pybel.examples import egf_graph as g
from pybel.schema import is_valid_edge, is_valid_node
import pymongo
from pymongo.collection import Collection


client = pymongo.MongoClient()


def to_mongodb(graph: pybel.BELGraph, db_name: str, collection_name: str) -> Collection:
    """Export the given BELGraph to a MongoDB.

    In order to use this function, MongoDB must already be running locally.

    :param graph: the graph to be exported
    :param db_name: the name of the MongoDB to which the graph should be exported
    :param collection_name: the name of the collection within the MongoDB where the graph will be stored.
    :return: the collection that now stores the graph
    """
    # Access (or create) the specified database and collection
    db = client[db_name]
    collection = db[collection_name]
    # If a collection with the same name already exists, drop its contents
    collection.drop()

    # Add the nodes
    for node in graph:
        if not is_valid_node(node):
            # TODO: Raise/log on invalid node
            pass
        # Add a 'type' parameter to avoid confusing nodes and links
        n = copy.deepcopy(node)
        n['type'] = 'node'
        collection.insert_one(n)

    # Add the edges
    edges = pybel.to_nodelink(graph)['links']
    for edge in edges:
        if not is_valid_edge(edge):
            # TODO: Raise/log on invalid edge
            pass
        # Add a 'type' parameter to avoid confusing nodes and links
        e = copy.deepcopy(edge)
        e['type'] = 'link'
        collection.insert_one(e)

    return collection


def find_nodes(
    collection: Collection,
    name: str = None,
    identifier: str = None,
    variants: List[pybel.dsl.EntityVariant] = None,
) -> List[Mapping[str, Any]]:
    """Find all the nodes that match the given criteria from a MongoDB Collection where a graph is stored.

    :param collection: A MongoDB collection within a database where a PyBEL graph has been stored
    :param name: The name of the desired node
    :param identifier: The identifier of the desired node
    :param variants: A list of variants that the desired node should contain. Note: nodes that contain the variants in addition to specified variants will be matched.
    :return: A list containing all the nodes that match the given criteria
    """
    if not (name or identifier):
        raise ValueError("Either a 'name' or 'identifier' is required to find a node.")
    filter_ = {'type': 'node'}
    if name:
        filter_['concept.name'] = name
    if identifier:
        filter_['concept.identifier'] = identifier
    if variants:
        filter_['variants'] = variants

    return collection.find(filter_)


def get_edges(
    collection: Collection,
    node: Mapping[str, Any] = None,
    node_name: str = None,
    node_identifier: str = None,
    node_variants: List[pybel.dsl.EntityVariant] = None,
) -> List[Tuple[Mapping[str, Any], List[Mapping[str, Any]]]]:
    """
    Get all the edges for nodes that match the given criteria and return in a list of tuples.

    Either a specific node or criteria (name, identifier, variants) that a desired node matches can be passed to this function. If a specific node is passed,
    the function will find all the edges for that node; if not, the function will find all nodes that match the criteria and and find all edges for those matching nodes.

    :param collection: A MongoDB collection within a database where a PyBEL graph has been stored
    :param node: The node whose edges should be found.
    :param name: The name of the desired node
    :param identifier: The identifier of the desired node
    :param variants: A list of variants that the desired node should contain. Note: nodes that contain the variants in addition to specified variants will be matched.
    :return: A list of tuples. The first element of each tuple is the node, and the second element is a list of all the edges for that node.
    """
    if not (node or node_name or node_identifier):
        raise ValueError("Either a specific node, 'node_name', or 'node_identifier' is required to get edges.")
    matching_nodes = []
    # If the `node` parameter is None or is an invalid node
    if not node or not is_valid_node(node):
        # If a node was present, TODO: log that an invalid node was passed
        if node:
            pass
        # Otherwise, no node was passed, so find all the nodes that match the given criteria
        matching_nodes = find_nodes(collection, name=node_name, identifier=node_identifier, variants=node_variants)
    # If a valid node was passed
    else:
        # Search only for that node in the graph
        matching_nodes = [node]

    edges = []
    for node in matching_nodes:
        # Remove the _id and type properties from the node (since they won't be included in the edge source/target information)
        n = copy.deepcopy(node)
        del n['_id'], n['type']
        # Find all the links where either the source or the target is node n
        filter_ = {'type': 'link', '$or': [{'source': n}, {'target': n}]}
        # Append (node n, [edge1, edge2...]) to edges
        edges.append((n, list(collection.find(filter_))))
    return edges
