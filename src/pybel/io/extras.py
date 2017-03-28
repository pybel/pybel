# -*- coding: utf-8 -*-

"""

PyBEL provides functions for input and output to several formats. This includes:

- BEL Script (*.bel)
- Pickle object (*.pickle)
- GraphML (*.graphml)
- JSON (*.json)
- Edge list (*.csv)
- Relational database
- Neo4J graph database

It also includes utilities to handle bytes, line iterators, and fetching data from URL.

"""

import json
import logging

import networkx as nx
import py2neo

from ..canonicalize import decanonicalize_node, calculate_canonical_name
from ..constants import PYBEL_CONTEXT_TAG, FUNCTION, NAME, RELATION
from ..graph import BELGraph
from ..utils import flatten_dict, flatten_graph_data

__all__ = [
    'to_graphml',
    'to_csv',
    'to_neo4j'
]

log = logging.getLogger(__name__)


def to_graphml(graph, file):
    """Writes this graph to GraphML XML file. The .graphml extension is suggested so Cytoscape can recognize it.

    :param graph: A BEL graph
    :type graph: BELGraph
    :param file: A file or file-like object
    :type file: file
    """
    g = nx.MultiDiGraph()

    for node, data in graph.nodes(data=True):
        g.add_node(node, json=json.dumps(data))

    for u, v, key, data in graph.edges(data=True, keys=True):
        g.add_edge(u, v, key=key, attr_dict=flatten_dict(data))

    nx.write_graphml(g, file)


def to_csv(graph, file, delimiter='\t', encoding='utf-8'):
    """Writes the graph as an edge list using :func:`networkx.write_edgelist`

    :param graph: A BEL graph
    :type graph: BELGraph
    :param file: A file or filelike object
    :type file: file
    :param delimiter: The output CSV delimiter. Defaults to tab
    :type delimiter: str
    :param encoding: The output format. Defaults to 'utf-8'
    :type encoding: str
    """
    nx.write_edgelist(flatten_graph_data(graph), file, data=True, delimiter=delimiter, encoding=encoding)


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
