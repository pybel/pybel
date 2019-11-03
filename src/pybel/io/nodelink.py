# -*- coding: utf-8 -*-

"""Conversion functions for BEL graphs with Node-Link JSON."""

import json
from itertools import chain, count
from operator import methodcaller
from typing import Any, Mapping, TextIO, Union

from networkx.utils import open_file

from .utils import ensure_version
from ..constants import GRAPH_ANNOTATION_LIST, MEMBERS, PRODUCTS, REACTANTS
from ..dsl import BaseEntity
from ..struct import BELGraph
from ..tokens import parse_result_to_dsl
from ..utils import tokenize_version

__all__ = [
    'to_nodelink',
    'to_nodelink_file',
    'to_nodelink_jsons',
    'from_nodelink',
    'from_nodelink_file',
    'from_nodelink_jsons',
]


def to_nodelink(graph: BELGraph) -> Mapping[str, Any]:
    """Convert this graph to a Node-Link JSON object."""
    graph_json_dict = _to_nodelink_json_helper(graph)

    # Convert annotation list definitions (which are sets) to canonicalized/sorted lists
    graph_json_dict['graph'][GRAPH_ANNOTATION_LIST] = {
        keyword: list(sorted(values))
        for keyword, values in graph_json_dict['graph'].get(GRAPH_ANNOTATION_LIST, {}).items()
    }

    return graph_json_dict


@open_file(1, mode='w')
def to_nodelink_file(graph: BELGraph, path: Union[str, TextIO], **kwargs) -> None:
    """Write this graph as Node-Link JSON to a file.

    :param graph: A BEL graph
    :param path: A path or file-like
    """
    graph_json_dict = to_nodelink(graph)
    json.dump(graph_json_dict, path, ensure_ascii=False, **kwargs)


def to_nodelink_jsons(graph: BELGraph, **kwargs) -> str:
    """Dump this graph as a Node-Link JSON object to a string."""
    graph_json_str = to_nodelink(graph)
    return json.dumps(graph_json_str, ensure_ascii=False, **kwargs)


def from_nodelink(graph_json_dict: Mapping[str, Any], check_version: bool = True) -> BELGraph:
    """Build a graph from Node-Link JSON Object."""
    pybel_version = tokenize_version(graph_json_dict['graph']['pybel_version'])
    if pybel_version[1] < 14:  # if minor version is less than 14
        raise ValueError('Invalid NodeLink JSON from old version of PyBEL (v{}.{}.{})'.format(*pybel_version))
    graph = _from_nodelink_json_helper(graph_json_dict)
    return ensure_version(graph, check_version=check_version)


@open_file(0, mode='r')
def from_nodelink_file(path: Union[str, TextIO], check_version: bool = True) -> BELGraph:
    """Build a graph from the Node-Link JSON contained in the given file.

    :param path: A path or file-like
    """
    graph_json_dict = json.load(path)
    return from_nodelink(graph_json_dict, check_version=check_version)


def from_nodelink_jsons(graph_json_str: str, check_version: bool = True) -> BELGraph:
    """Read a BEL graph from a Node-Link JSON string."""
    graph_json_dict = json.loads(graph_json_str)
    return from_nodelink(graph_json_dict, check_version=check_version)


def _to_nodelink_json_helper(graph: BELGraph) -> Mapping[str, Any]:
    """Convert a BEL graph to a node-link format.

    Adapted from :func:`networkx.readwrite.json_graph.node_link_data`
    """
    nodes = sorted(graph, key=methodcaller('as_bel'))

    mapping = dict(zip(nodes, count()))

    return {
        'directed': True,
        'multigraph': True,
        'graph': graph.graph.copy(),
        'nodes': [
            _augment_node(node)
            for node in nodes
        ],
        'links': [
            dict(
                chain(
                    data.copy().items(),
                    [('source', mapping[u]), ('target', mapping[v]), ('key', key)],
                ),
            )
            for u, v, key, data in graph.edges(keys=True, data=True)
        ],
    }


def _augment_node(node: BaseEntity) -> BaseEntity:
    """Add the SHA-512 identifier to a node's dictionary."""
    rv = node.copy()
    rv['id'] = node.md5
    rv['bel'] = node.as_bel()
    for m in chain(node.get(MEMBERS, []), node.get(REACTANTS, []), node.get(PRODUCTS, [])):
        m.update(_augment_node(m))
    return rv


def _from_nodelink_json_helper(data: Mapping[str, Any]) -> BELGraph:
    """Return graph from node-link data format.

    Adapted from :func:`networkx.readwrite.json_graph.node_link_graph`
    """
    graph = BELGraph()
    graph.graph = data.get('graph', {})
    graph.graph[GRAPH_ANNOTATION_LIST] = {
        keyword: set(values)
        for keyword, values in graph.graph.get(GRAPH_ANNOTATION_LIST, {}).items()
    }

    mapping = []

    for node_data in data['nodes']:
        node = parse_result_to_dsl(node_data)
        graph.add_node_from_data(node)
        mapping.append(node)

    for data in data['links']:
        u = mapping[data['source']]
        v = mapping[data['target']]

        edge_data = {
            k: v
            for k, v in data.items()
            if k not in {'source', 'target', 'key'}
        }
        graph.add_edge(u, v, key=data['key'], **edge_data)

    return graph
