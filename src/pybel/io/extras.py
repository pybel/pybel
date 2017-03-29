# -*- coding: utf-8 -*-

"""This module contains IO functions for outputting BEL graphs to lossy formats, such as GraphML and CSV"""

import json
import logging

import networkx as nx

from ..graph import BELGraph
from ..utils import flatten_dict, flatten_graph_data

__all__ = [
    'to_graphml',
    'to_csv'
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
