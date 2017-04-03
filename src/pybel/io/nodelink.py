# -*- coding: utf-8 -*-

"""This module contains IO functions for interconversion between BEL graphs and node-link JSON"""

import json
import os

from networkx.readwrite.json_graph import node_link_data, node_link_graph

from .utils import ensure_version
from ..constants import GRAPH_ANNOTATION_LIST
from ..graph import BELGraph
from ..utils import list2tuple

__all__ = [
    'to_json_dict',
    'to_json',
    'to_jsons',
    'from_json_dict',
    'from_json',
    'from_jsons',
]


def to_json_dict(graph):
    """Converts this graph to a node-link JSON object

    :param graph: A BEL graph
    :type graph: BELGraph
    :return: A node-link JSON object representing the given graph
    :rtype: dict
    """
    data = node_link_data(graph)
    data['graph'][GRAPH_ANNOTATION_LIST] = {k: list(sorted(v)) for k, v in
                                            data['graph'].get(GRAPH_ANNOTATION_LIST, {}).items()}
    return data


def to_json(graph, file):
    """Writes this graph as a node-link JSON object

    :param graph: A BEL graph
    :type graph: BELGraph
    :param file: A write-supporting file or file-like object
    :type file: file
    """
    json_dict = to_json_dict(graph)
    json.dump(json_dict, file, ensure_ascii=False)


def to_jsons(graph):
    """Dumps this graph as a node-link JSON object to a string

    :param graph: A BEL graph
    :type graph: BELGraph
    :return: A string representation of the node-link JSON produced for this graph by :func:`to_json_dict`
    :rtype: str
    """
    return json.dumps(to_json_dict(graph), ensure_ascii=False)


def from_json_dict(data, check_version=True):
    """Reads graph from node-link JSON Object

    :param data: A JSON dictionary representing a graph
    :type data: dict
    :param check_version: Checks if the graph was produced by this version of PyBEL
    :type check_version: bool
    :return: A BEL graph
    :rtype: BELGraph
    """

    for i, node in enumerate(data['nodes']):
        data['nodes'][i]['id'] = list2tuple(data['nodes'][i]['id'])

    graph = node_link_graph(data, directed=True, multigraph=True)
    graph = BELGraph(data=graph)
    return ensure_version(graph, check_version=check_version)


def from_json(path, check_version=True):
    """Reads graph from node-link JSON object

    :param path: file path to read
    :type path: str
    :param check_version: Checks if the graph was produced by this version of PyBEL
    :type check_version: bool
    :return: A BEL graph
    :rtype: BELGraph
    """
    with open(os.path.expanduser(path)) as f:
        json_dict = json.load(f)
        graph = from_json_dict(json_dict, check_version=check_version)
        return graph


def from_jsons(s, check_version=True):
    """Reads a BEL graph from a node-link JSON string

    :param s: A node-link JSON string produced by PyBEL
    :type s: str
    :param check_version: Checks if the graph was produced by this version of PyBEL
    :type check_version: bool
    :return: A BEL graph
    :rtype: BELGraph
    """
    json_dict = json.loads(s)
    graph = from_json_dict(json_dict, check_version=check_version)
    return graph
