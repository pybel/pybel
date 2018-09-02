# -*- coding: utf-8 -*-

"""Output functions for BEL graphs to Neo4j."""

from six import string_types
from tqdm import tqdm

from ..constants import (
    ANNOTATIONS, CITATION, CITATION_REFERENCE, CITATION_TYPE, EVIDENCE, FUSION, MEMBERS, NAMESPACE, OBJECT,
    RELATION, SUBJECT, VARIANTS,
)
from ..utils import flatten_dict

__all__ = [
    'to_neo4j',
]


def to_neo4j(graph, neo_connection, use_tqdm=False):
    """Upload a BEL graph to a Neo4j graph database using :mod:`py2neo`.

    :param pybel.BELGraph graph: A BEL Graph
    :param neo_connection: A :mod:`py2neo` connection object. Refer to the
     `py2neo documentation <http://py2neo.org/v3/database.html#the-graph>`_ for how to build this object.
    :type neo_connection: str or py2neo.Graph

    Example Usage:

    >>> import py2neo
    >>> import pybel
    >>> from pybel.examples import sialic_acid_graph
    >>> neo_graph = py2neo.Graph("http://localhost:7474/db/data/")  # use your own connection settings
    >>> pybel.to_neo4j(sialic_acid_graph, neo_graph)
    """
    import py2neo

    if isinstance(neo_connection, string_types):
        neo_connection = py2neo.Graph(neo_connection)

    tx = neo_connection.begin()

    node_map = {}

    nodes = graph.nodes(data=True)
    if use_tqdm:
        nodes = tqdm(nodes, desc='nodes')

    for node, data in nodes:
        if NAMESPACE not in data or VARIANTS in data or MEMBERS in data or FUSION in data:
            attrs = {'name': data.as_bel()}
        else:
            attrs = {'namespace': data.namespace}

            if data.name and data.identifier:
                attrs['name'] = data.name
                attrs['identifier'] = data.identifier
            elif data.identifier and not data.name:
                attrs['name'] = data.identifier
            elif data.name and not data.identifier:
                attrs['name'] = data.name

        node_map[node] = py2neo.Node(data.function, **attrs)

        tx.create(node_map[node])

    edges = graph.edges(keys=True, data=True)
    if use_tqdm:
        edges = tqdm(edges, desc='edges')

    for u, v, key, data in edges:
        rel_type = data[RELATION]

        d = data.copy()
        del d[RELATION]

        attrs = {}

        annotations = d.pop(ANNOTATIONS, None)
        if annotations:
            for annotation, values in annotations.items():
                attrs[annotation] = list(values)

        citation = d.pop(CITATION, None)
        if citation:
            attrs[CITATION] = '{}:{}'.format(citation[CITATION_TYPE], citation[CITATION_REFERENCE])

        if EVIDENCE in d:
            attrs[EVIDENCE] = d[EVIDENCE]

        for side in (SUBJECT, OBJECT):
            side_data = d.get(side)
            if side_data:
                attrs.update(flatten_dict(side_data, parent_key=side))

        rel = py2neo.Relationship(node_map[u], rel_type, node_map[v], key=key, **attrs)
        tx.create(rel)

    tx.commit()
