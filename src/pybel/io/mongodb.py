# -*- coding: utf-8 -*-

"""An exporter from PyBEL graphs to a local Mongo database."""

import logging
from copy import deepcopy
from typing import Any, List, Mapping, Optional, Tuple

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from .sbel import to_sbel
from ..constants import (
    CONCEPT, FUNCTION, IDENTIFIER,
    NAME, SOURCE, TARGET, VARIANTS,
)
from ..dsl import Variant
from ..schema import is_valid_edge, is_valid_node
from ..struct import BELGraph

__all__ = [
    '_rm_mongo_keys',
    'to_mongodb',
    'find_nodes',
    'get_edges_from_node',
    'get_edges_from_criteria'
]

logger = logging.getLogger(__name__)

# Define some reused values
DB_NAME = 'pybel_graphs'
COLLECTION_NAME = 'collection'

TYPE = 'type'
ID = '_id'
NODE = 'node'
LINK = 'link'


def _default_collection_name(database: Database):
    """Get a valid (unused) default collection name."""
    idx = 1
    collection_name = COLLECTION_NAME
    while database[collection_name].find_one() is not None:
        # Naming convention is: collection_1, collection_2, etc
        collection_name = '_'.join((COLLECTION_NAME, str(idx)))
        idx += 1
    return collection_name


def to_mongodb(
    graph: BELGraph,
    db_name: Optional[str] = None,
    collection_name: Optional[str] = None,
    client: Optional[MongoClient] = None
) -> Collection:
    """Export the given BELGraph to a MongoDB.

    In order to use this function, MongoDB must already be running locally.

    :param graph: The graph to be exported
    :param db_name: An optional name of the MongoDB to which the graph should be exported
    :param collection_name: An optional name of the collection within the MongoDB where the graph will be stored.
    :param client: An optional MongoClient object to use instead of a default
    :return: the collection that now stores the graph
    """
    if client is None:
        client = MongoClient()
    if db_name is None:
        db_name = DB_NAME
    # Access (or create) the specified database
    db = client[db_name]
    # If no collection_name was passed
    if collection_name is None:
        # Attempt to create collections until a unique name is found
        collection_name = _default_collection_name(db)
    # Access (or create) the specified collection
    collection = db[collection_name]
    # If a collection with the same name already exists, drop its contents
    collection.drop()

    # Store all the nodes/edges in a list to be bulk added
    documents = []

    # Add the nodes to documents
    for node in graph:
        if not is_valid_node(node):
            logger.warning(f'Invalid node encountered: {node}')
        # Add a 'type' parameter to avoid confusing nodes and links
        n = deepcopy(node)
        n[TYPE] = NODE
        documents.append(n)

    # Add the edges to documents
    edges = to_sbel(graph, yield_metadata=False)
    for edge in edges:
        if not is_valid_edge(edge):
            logger.warning(f'Invalid edge encountered: {edge}')
        # Add a 'type' parameter to avoid confusing nodes and links
        e = deepcopy(edge)
        e[TYPE] = LINK
        documents.append(e)
    # Insert the documents into the collection
    collection.insert_many(documents)
    return collection


def find_nodes(
    collection: Collection,
    name: str = None,
    identifier: str = None,
    function: str = None,
    variants: List[Variant] = None,
) -> List[Mapping[str, Any]]:
    """Find all the nodes that match the given criteria from a MongoDB Collection where a graph is stored.

    :param collection: A MongoDB collection within a database where a PyBEL graph has been stored
    :param name: The name of the desired node
    :param identifier: The identifier of the desired node
    :param function: The type of the desired node ("protein", "complex", etc)
    :param variants: A list of variants that the desired node should contain.
     Note: nodes that contain the variants in addition to specified variants will be matched.
    :return: A list containing all the nodes that match the given criteria
    """
    if not (name or identifier):
        raise ValueError("Either a 'name' or 'identifier' is required to find a node.")
    # The mongo .find() method requires that sub-elements be notated 'parent.child'
    concept_name = '.'.join((CONCEPT, NAME))
    concept_identifier = '.'.join((CONCEPT, IDENTIFIER))
    filter_ = {
        TYPE: NODE,
        concept_name: name,
        concept_identifier: identifier,
        FUNCTION: function,
        VARIANTS: variants,
    }
    for key, value in list(filter_.items()):
        if not value:
            del filter_[key]

    return list(collection.find(filter_))


def _rm_mongo_keys(item: dict):
    """Remove any dictionary keys used for internal MongoDB identification from the items.

    :param item: A dictionary representing a node or an edge from a MongoDB collection
    """
    for prop in (ID, TYPE):
        if prop in item.keys():
            del item[prop]


def get_edges_from_node(collection: Collection, node: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    """Return all the edges for the given node.

    :param collection: A MongoDB collection within a database where a PyBEL graph has been stored
    :param node: The node whose edges should be returned
    :return: A list of the edges pointing to or from the given node
    """
    if not is_valid_node(node):
        raise ValueError("Invalid node ", node)
    # Remove the _id and type properties from the node (since they won't be included in the edge source/target information)
    n = deepcopy(node)
    _rm_mongo_keys(n)
    # Find all the links where either the source or the target is node n
    filter_ = {TYPE: LINK, '$or': [{SOURCE: n}, {TARGET: n}]}
    return list(collection.find(filter_))


def get_edges_from_criteria(
    collection: Collection,
    node_name: str = None,
    node_identifier: str = None,
    node_function: str = None,
    node_variants: List[Variant] = None,
) -> List[Tuple[Mapping[str, Any], List[Mapping[str, Any]]]]:
    """Get all the edges for nodes that match the given criteria and return in a list of tuples.

    :param collection: A MongoDB collection within a database where a PyBEL graph has been stored
    :param name: The name of the desired node
    :param identifier: The identifier of the desired node
    :param function: The type of the desired node ("protein", "complex", etc)
    :param variants: A list of variants that the desired node should contain.
     Note: nodes that contain the variants in addition to specified variants will be matched.
    :return: A list of tuples. The first element of each tuple is the node, and the second element is a list of the edges.
    """
    if not (node_name or node_identifier):
        raise ValueError("Either a name or an identifier is required to get edges.")
    matching_nodes = find_nodes(
        collection,
        name=node_name,
        identifier=node_identifier,
        function=node_function,
        variants=node_variants
    )
    edges = []
    for node in matching_nodes:
        matching_edges = get_edges_from_node(collection, node)
        # Append (node, [edge1, edge2...]) to edges
        edges.append((node, matching_edges))
    return edges
