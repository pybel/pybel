# -*- coding: utf-8 -*-

"""Output functions for BEL graphs to Neo4j."""

import json

from tqdm import tqdm

from ..constants import (
    ANNOTATIONS, CITATION, CONCEPT, EVIDENCE, FUSION, MEMBERS, RELATION, SOURCE_MODIFIER, TARGET_MODIFIER, VARIANTS,
)
from ..struct.graph import BELGraph
from ..utils import flatten_dict

__all__ = [
    'to_neo4j',
]


def to_neo4j(graph: BELGraph, neo_connection=None, use_tqdm: bool = True, period: int = 1000):
    """Upload a BEL graph to a Neo4j graph database using :mod:`py2neo`.

    :param graph: A BEL Graph
    :param neo_connection: A :mod:`py2neo` connection object. Refer to the
     `py2neo documentation <http://py2neo.org/v3/database.html#the-graph>`_ for how to build this object.
    :type neo_connection: None or str or py2neo.Graph

    Example Usage:

    >>> import py2neo
    >>> import pybel
    >>> from pybel.examples import sialic_acid_graph
    >>> neo_graph = py2neo.Graph("bolt://localhost:7687")  # use your own connection settings
    >>> pybel.to_neo4j(sialic_acid_graph, neo_graph)
    """
    import py2neo

    if neo_connection is None:
        neo_connection = 'bolt://localhost:7687'
    if isinstance(neo_connection, str):
        neo_connection = py2neo.Graph(neo_connection)

    tx = neo_connection.begin()

    node_map = {}

    nodes = list(graph)
    if use_tqdm:
        nodes = tqdm(nodes, desc='nodes')

    for i, node in enumerate(nodes, start=1):
        if CONCEPT not in node or VARIANTS in node or MEMBERS in node or FUSION in node:
            attrs = {'name': node.as_bel()}
        else:
            attrs = {'namespace': node.namespace, 'data': json.dumps(node)}

            if node.name and node.identifier:
                attrs['name'] = node.name
                attrs['identifier'] = node.identifier
            elif node.identifier and not node.name:
                attrs['name'] = node.identifier
            elif node.name and not node.identifier:
                attrs['name'] = node.name

        node_map[node] = py2neo.Node(node.function, **attrs)
        tx.create(node_map[node])

        if 0 == i % period:
            tx.commit()
            tx = neo_connection.begin()

    edges = graph.edges(keys=True, data=True)
    if use_tqdm:
        edges = tqdm(edges, desc='edges')

    for i, (u, v, key, edge_data) in enumerate(edges, start=1):
        attrs = {'data': json.dumps(edge_data)}

        rel_type = edge_data[RELATION]

        for annotation, values in edge_data.get(ANNOTATIONS, {}).items():
            attrs[annotation] = list(values)

        citation = edge_data.get(CITATION)
        if citation:
            attrs[CITATION] = citation.curie

        evidence = edge_data.get(EVIDENCE)
        if evidence:
            attrs[EVIDENCE] = evidence

        for side in (SOURCE_MODIFIER, TARGET_MODIFIER):
            side_data = edge_data.get(side)
            if side_data:
                attrs.update(flatten_dict(side_data, parent_key=side))

        rel = py2neo.Relationship(node_map[u], rel_type, node_map[v], key=key, **attrs)
        tx.create(rel)

        if 0 == i % period:
            tx.commit()
            tx = neo_connection.begin()

    tx.commit()
    return neo_connection
