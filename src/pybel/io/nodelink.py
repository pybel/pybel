# -*- coding: utf-8 -*-

"""

Node-Link JSON
--------------
This module contains IO functions for interconversion between BEL graphs and Node-Link JSON

"""

import json
import os
from itertools import chain

from .utils import ensure_version
from ..constants import GRAPH_ANNOTATION_LIST, GRAPH_UNCACHED_NAMESPACES
from ..struct import BELGraph
from ..utils import list2tuple

__all__ = [
    'to_json',
    'to_json_file',
    'to_json_path',
    'to_jsons',
    'from_json',
    'from_json_file',
    'from_json_path',
    'from_jsons',
]

_attrs = dict(
    source='source',
    target='target',
    name='id',
    key='key',
    link='links'
)


def node_link_data(G):
    attrs = _attrs
    name = attrs['name']
    source = attrs['source']
    target = attrs['target']
    links = attrs['link']
    # Allow 'key' to be omitted from attrs if the graph is not a multigraph.
    key = attrs['key']

    data = {
        'graph': G.graph,
        'nodes': [
            dict(chain(G.nodes[n].items(), [(name, n)]))
            for n in G
        ]
    }
    data[links] = [
        dict(chain(d.items(), ((source, u), (target, v), (key, k))))
        for u, v, k, d in G.edges(keys=True, data=True)
    ]
    return data


def node_link_graph(data):
    attrs = _attrs
    graph = BELGraph()
    name = attrs['name']
    source = attrs['source']
    target = attrs['target']
    links = attrs['link']
    key = attrs['key']

    graph.graph = data['graph']

    for d in data['nodes']:
        node = list2tuple(d[name])
        nodedata = dict((k, v) for k, v in d.items() if k != name)
        graph.add_node(node, **nodedata)

    for d in data[links]:
        src = list2tuple(d[source])
        tgt = list2tuple(d[target])
        ky = d.get(key, None)
        edgedata = dict((k, v) for k, v in d.items()
                        if k != source and k != target and k != key)
        graph.add_edge(src, tgt, ky, **edgedata)

    return graph


def to_json(graph):
    """Converts this graph to a Node-Link JSON object

    :param BELGraph graph: A BEL graph
    :return: A Node-Link JSON object representing the given graph
    :rtype: dict
    """
    graph_json_dict = node_link_data(graph)
    graph_json_dict['graph'][GRAPH_ANNOTATION_LIST] = {
        k: list(sorted(v))
        for k, v in graph_json_dict['graph'][GRAPH_ANNOTATION_LIST].items()
    }
    graph_json_dict['graph'][GRAPH_UNCACHED_NAMESPACES] = list(graph_json_dict['graph'][GRAPH_UNCACHED_NAMESPACES])

    return graph_json_dict


def to_json_path(graph, path, **kwargs):
    """Writes this graph to the given path as a Node-Link JSON

    :param BELGraph graph: A BEL graph
    :param str path: A file path
    """
    with open(os.path.expanduser(path), 'w') as f:
        return to_json_file(graph, file=f, **kwargs)


def to_json_file(graph, file, **kwargs):
    """Writes this graph as Node-Link JSON to a file

    :param BELGraph graph: A BEL graph
    :param file file: A write-supporting file or file-like object
    """
    graph_json_dict = to_json(graph)
    json.dump(graph_json_dict, file, ensure_ascii=False, **kwargs)


def to_jsons(graph, **kwargs):
    """Dumps this graph as a Node-Link JSON object to a string

    :param BELGraph graph: A BEL graph
    :return: A string representation of the Node-Link JSON produced for this graph by :func:`pybel.to_json`
    :rtype: str
    """
    graph_json_str = to_json(graph)
    return json.dumps(graph_json_str, ensure_ascii=False, **kwargs)


def from_json(graph_json_dict, check_version=True):
    """Builds a graph from Node-Link JSON Object

    :param dict graph_json_dict: A JSON dictionary representing a graph
    :param bool check_version: Checks if the graph was produced by this version of PyBEL
    :rtype: BELGraph
    """
    for i, node in enumerate(graph_json_dict['nodes']):
        graph_json_dict['nodes'][i]['id'] = list2tuple(graph_json_dict['nodes'][i]['id'])

    graph = node_link_graph(graph_json_dict)
    return ensure_version(graph, check_version=check_version)


def from_json_path(path, check_version=True):
    """Builds a graph from a file containing Node-Link JSON

    :param str path: A file path. Expands user.
    :param bool check_version: Checks if the graph was produced by this version of PyBEL
    :rtype: BELGraph
    """
    with open(os.path.expanduser(path)) as f:
        return from_json_file(f, check_version=check_version)


def from_json_file(file, check_version=True):
    """Builds a graph from the Node-Link JSON contained in the given file

    :param file file: A readable file or file-like
    :param bool check_version: Checks if the graph was produced by this version of PyBEL
    :rtype: BELGraph
    """
    graph_json_dict = json.load(file)
    return from_json(graph_json_dict, check_version=check_version)


def from_jsons(graph_json_str, check_version=True):
    """Reads a BEL graph from a Node-Link JSON string

    :param str graph_json_str: A Node-Link JSON string produced by PyBEL
    :param bool check_version: Checks if the graph was produced by this version of PyBEL
    :rtype: BELGraph
    """
    graph_json_dict = json.loads(graph_json_str)
    return from_json(graph_json_dict, check_version=check_version)
