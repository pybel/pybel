# -*- coding: utf-8 -*-

"""This module contains IO functions for outputting BEL graphs to a Neo4J graph database"""

import py2neo

from ..canonicalize import calculate_canonical_name, decanonicalize_node
from ..constants import FUNCTION, NAME, RELATION, PYBEL_CONTEXT_TAG
from ..utils import flatten_dict

__all__ = ['to_neo4j']


def to_neo4j(graph, neo_graph, context=None):
    """Uploads a BEL graph to Neo4J graph database using `py2neo`

    :param graph: A BEL Graph
    :type graph: BELGraph
    :param neo_graph: A py2neo graph object, Refer to the
                        `py2neo documentation <http://py2neo.org/v3/database.html#the-graph>`_
                        for how to build this object.
    :type neo_graph: :class:`py2neo.Graph`
    :param context: A disease context to allow for multiple disease models in one neo4j instance.
                    Each edge will be assigned an attribute :code:`pybel_context` with this value
    :type context: str
    
    Example Usage:
    
    >>> import pybel, py2neo
    >>> url = 'http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel'
    >>> g = pybel.from_url(url)
    >>> neo_graph = py2neo.Graph("http://localhost:7474/db/data/")  # use your own connection settings
    >>> pybel.to_neo4j(g, neo_graph)
    """
    tx = neo_graph.begin()

    node_map = {}
    for node, data in graph.nodes(data=True):
        node_type = data[FUNCTION]
        attrs = {k: v for k, v in data.items() if k not in {FUNCTION, NAME}}

        if NAME in data:
            attrs['identifier'] = data[NAME]
            attrs['name'] = calculate_canonical_name(graph, node)

        node_map[node] = py2neo.Node(node_type, bel=decanonicalize_node(graph, node), **attrs)

        tx.create(node_map[node])

    for u, v, data in graph.edges(data=True):
        neo_u = node_map[u]
        neo_v = node_map[v]
        rel_type = data[RELATION]
        attrs = flatten_dict(data)
        if context is not None:
            attrs[PYBEL_CONTEXT_TAG] = str(context)
        rel = py2neo.Relationship(neo_u, rel_type, neo_v, **attrs)
        tx.create(rel)

    tx.commit()
