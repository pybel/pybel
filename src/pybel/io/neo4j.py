# -*- coding: utf-8 -*-

"""

Neo4j
~~~~~
This module contains IO functions for outputting BEL graphs to a Neo4J graph database

"""

from ..canonicalize import calculate_canonical_name, decanonicalize_node
from ..constants import FUNCTION, NAME, RELATION, PYBEL_CONTEXT_TAG
from ..utils import flatten_dict

__all__ = ['to_neo4j']


def to_neo4j(graph, neo_connection, context=None):
    """Uploads a BEL graph to Neo4J graph database using :mod:`py2neo`

    :param BELGraph graph: A BEL Graph
    :param neo_connection: A :mod:`py2neo` connection object. Refer to the
                          `py2neo documentation <http://py2neo.org/v3/database.html#the-graph>`_
                          for how to build this object.
    :type neo_connection: :class:`py2neo.Graph`
    :param str context: A disease context to allow for multiple disease models in one neo4j instance.
                        Each edge will be assigned an attribute :code:`pybel_context` with this value
    
    Example Usage:
    
    >>> import pybel, py2neo
    >>> url = 'http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel'
    >>> g = pybel.from_url(url)
    >>> neo_graph = py2neo.Graph("http://localhost:7474/db/data/")  # use your own connection settings
    >>> pybel.to_neo4j(g, neo_graph)
    """
    import py2neo

    tx = neo_connection.begin()

    node_map = {}
    for node, data in graph.nodes(data=True):
        node_type = data[FUNCTION]
        attrs = {k: v for k, v in data.items() if k not in {FUNCTION, NAME}}
        attrs['name'] = calculate_canonical_name(graph, node)

        if NAME in data:
            attrs['identifier'] = data[NAME]

        node_map[node] = py2neo.Node(node_type, bel=decanonicalize_node(graph, node), **attrs)

        tx.create(node_map[node])

    for u, v, data in graph.edges(data=True):
        rel_type = data[RELATION]
        attrs = flatten_dict(data)
        if context is not None:
            attrs[PYBEL_CONTEXT_TAG] = str(context)
        rel = py2neo.Relationship(node_map[u], rel_type, node_map[v], **attrs)
        tx.create(rel)

    tx.commit()
