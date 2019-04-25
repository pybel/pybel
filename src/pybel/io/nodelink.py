# -*- coding: utf-8 -*-

"""Conversion functions for BEL graphs with Node-Link JSON."""

import json
import os
from itertools import chain, count
from operator import methodcaller
from typing import Any, Mapping, TextIO

from .utils import ensure_version
from ..constants import GRAPH_ANNOTATION_LIST, GRAPH_UNCACHED_NAMESPACES, MEMBERS, PRODUCTS, REACTANTS
from ..dsl import BaseEntity
from ..struct import BELGraph
from ..tokens import parse_result_to_dsl

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


def to_json(graph: BELGraph) -> Mapping[str, Any]:
    """Convert this graph to a Node-Link JSON object."""
    graph_json_dict = node_link_data(graph)

    # Convert annotation list definitions (which are sets) to canonicalized/sorted lists
    graph_json_dict['graph'][GRAPH_ANNOTATION_LIST] = {
        keyword: list(sorted(values))
        for keyword, values in graph_json_dict['graph'].get(GRAPH_ANNOTATION_LIST, {}).items()
    }

    # Convert set to list
    graph_json_dict['graph'][GRAPH_UNCACHED_NAMESPACES] = list(
        graph_json_dict['graph'].get(GRAPH_UNCACHED_NAMESPACES, [])
    )

    return graph_json_dict


def to_json_path(graph: BELGraph, path: str, **kwargs) -> None:
    """Write this graph to the given path as a Node-Link JSON."""
    with open(os.path.expanduser(path), 'w') as f:
        to_json_file(graph, file=f, **kwargs)


def to_json_file(graph: BELGraph, file: TextIO, **kwargs) -> None:
    """Write this graph as Node-Link JSON to a file."""
    graph_json_dict = to_json(graph)
    json.dump(graph_json_dict, file, ensure_ascii=False, **kwargs)


def to_jsons(graph: BELGraph, **kwargs) -> str:
    """Dump this graph as a Node-Link JSON object to a string."""
    graph_json_str = to_json(graph)
    return json.dumps(graph_json_str, ensure_ascii=False, **kwargs)


def from_json(graph_json_dict: Mapping[str, Any], check_version=True) -> BELGraph:
    """Build a graph from Node-Link JSON Object."""
    graph = node_link_graph(graph_json_dict)
    return ensure_version(graph, check_version=check_version)


def from_json_path(path: str, check_version: bool = True) -> BELGraph:
    """Build a graph from a file containing Node-Link JSON."""
    with open(os.path.expanduser(path)) as f:
        return from_json_file(f, check_version=check_version)


def from_json_file(file: TextIO, check_version=True) -> BELGraph:
    """Build a graph from the Node-Link JSON contained in the given file."""
    graph_json_dict = json.load(file)
    return from_json(graph_json_dict, check_version=check_version)


def from_jsons(graph_json_str: str, check_version: bool = True) -> BELGraph:
    """Read a BEL graph from a Node-Link JSON string."""
    graph_json_dict = json.loads(graph_json_str)
    return from_json(graph_json_dict, check_version=check_version)


def node_link_data(graph: BELGraph) -> Mapping[str, Any]:
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
            dict(chain(
                data.copy().items(),
                [('source', mapping[u]), ('target', mapping[v]), ('key', key)]
            ))
            for u, v, key, data in graph.edges(keys=True, data=True)
        ]
    }


def _augment_node(node: BaseEntity) -> BaseEntity:
    """Add the SHA-512 identifier to a node's dictionary."""
    rv = node.copy()
    rv['id'] = node.as_sha512()
    rv['bel'] = node.as_bel()
    for m in chain(node.get(MEMBERS, []), node.get(REACTANTS, []), node.get(PRODUCTS, [])):
        m.update(_augment_node(m))
    return rv


def node_link_graph(data: Mapping[str, Any]) -> BELGraph:
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
        _dsl = parse_result_to_dsl(node_data)
        node = graph.add_node_from_data(_dsl)
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
