# -*- coding: utf-8 -*-

"""

Node-Link JSON
--------------
This module contains IO functions for interconversion between BEL graphs and Node-Link JSON

"""

import json

from networkx.readwrite.json_graph import node_link_data, node_link_graph

from .utils import ensure_version
from ..constants import GRAPH_ANNOTATION_LIST
from ..struct import BELGraph
from ..utils import list2tuple

__all__ = [
    'to_json',
    'to_json_file',
    'to_jsons',
    'from_json',
    'from_json_file',
    'from_jsons',
]


def to_json(graph):
    """Converts this graph to a Node-Link JSON object

    :param BELGraph graph: A BEL graph
    :return: A Node-Link JSON object representing the given graph
    :rtype: dict
    """
    graph_json_dict = node_link_data(graph)
    graph_json_dict['graph'][GRAPH_ANNOTATION_LIST] = {
        k: list(sorted(v))
        for k, v in graph_json_dict['graph'].get(GRAPH_ANNOTATION_LIST, {}).items()
    }
    return graph_json_dict


def to_json_file(graph, file):
    """Writes this graph as Node-Link JSON to a file

    :param BELGraph graph: A BEL graph
    :param file file: A write-supporting file or file-like object
    """
    graph_json_dict = to_json(graph)
    json.dump(graph_json_dict, file, ensure_ascii=False)


def to_jsons(graph):
    """Dumps this graph as a Node-Link JSON object to a string

    :param BELGraph graph: A BEL graph
    :return: A string representation of the Node-Link JSON produced for this graph by :func:`pybel.to_json`
    :rtype: str
    """
    graph_json_str = to_json(graph)
    return json.dumps(graph_json_str, ensure_ascii=False)


def from_json(graph_json_dict, check_version=True):
    """Builds a graph from Node-Link JSON Object

    :param dict graph_json_dict: A JSON dictionary representing a graph
    :param bool check_version: Checks if the graph was produced by this version of PyBEL
    :return: A BEL graph
    :rtype: BELGraph
    """
    for i, node in enumerate(graph_json_dict['nodes']):
        graph_json_dict['nodes'][i]['id'] = list2tuple(graph_json_dict['nodes'][i]['id'])

    graph = node_link_graph(graph_json_dict, directed=True, multigraph=True)
    graph = BELGraph(data=graph)
    return ensure_version(graph, check_version=check_version)


def from_json_file(file, check_version=True):
    """Builds a graph from the Node-Link JSON contained in the given file

    :param file file: A readable file or file-like
    :param bool check_version: Checks if the graph was produced by this version of PyBEL
    :return: A BEL graph
    :rtype: BELGraph
    """
    graph_json_dict = json.load(file)
    return from_json(graph_json_dict, check_version=check_version)


def from_jsons(graph_json_str, check_version=True):
    """Reads a BEL graph from a Node-Link JSON string

    :param str graph_json_str: A Node-Link JSON string produced by PyBEL
    :param bool check_version: Checks if the graph was produced by this version of PyBEL
    :return: A BEL graph
    :rtype: BELGraph
    """
    graph_json_dict = json.loads(graph_json_str)
    return from_json(graph_json_dict, check_version=check_version)
