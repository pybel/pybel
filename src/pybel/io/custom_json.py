# -*- coding: utf-8 -*-

"""Conversion functions for customized node-link JSON format prior canonicalization.

This module uses the 'pybel.canonicalize' module prior exporting to the node-link JSON format. This allows the inclusion
of modifiers in the nodes instead of the edges, the default schema in PyBEL.
"""

import json
from itertools import chain, count
from typing import Any, Mapping, TextIO, Union

from networkx.utils import open_file

from ..canonicalize import _decanonicalize_edge_node, edge_to_tuple
from ..constants import GRAPH_ANNOTATION_LIST, OBJECT, SUBJECT
from ..struct import BELGraph

__all__ = [
    'to_canonicalized_json',
]


def to_canonicalized_json(graph: BELGraph) -> Mapping[str, Any]:
    """Convert this graph to a node-link JSON object by previously canonicalizing the nodes.

    :param graph: BEL Graph
    """
    graph_json_dict = _canonicalize_helper(graph)

    # Convert annotation list definitions (which are sets) to canonicalized/sorted lists
    graph_json_dict['graph'][GRAPH_ANNOTATION_LIST] = {
        keyword: list(sorted(values))
        for keyword, values in graph_json_dict['graph'].get(GRAPH_ANNOTATION_LIST, {}).items()
    }

    return graph_json_dict


@open_file(1, mode='w')
def to_canonicalized_json_file(graph: BELGraph, path: Union[str, TextIO], **kwargs) -> None:
    """Write this graph as node-link JSON to a file.

    :param graph: A BEL graph
    :param path: A path or file-like
    """
    graph_json_dict = _canonicalize_helper(graph)
    json.dump(graph_json_dict, path, ensure_ascii=False, **kwargs)


def _canonicalize_helper(graph: BELGraph) -> Mapping[str, Any]:
    """Helper to canonicalize nodes.

    :param graph: BEL Graph
    """

    canonical_nodes = set()

    for u, v, data in graph.edges(data=True):
        canonical_u, _, canonical_v = edge_to_tuple(u, v, data)
        canonical_nodes.add(canonical_u)
        canonical_nodes.add(canonical_v)

    nodes = sorted(list(canonical_nodes))
    mapping = dict(zip(nodes, count()))

    return {
        'directed': True,
        'multigraph': True,
        'graph': graph.graph.copy(),
        'nodes': [
            node
            for node in nodes
        ],
        'links': [
            dict(
                chain(
                    data.copy().items(),
                    [
                        ('source', mapping[_decanonicalize_edge_node(u, data, node_position=SUBJECT)]),
                        ('target', mapping[_decanonicalize_edge_node(v, data, node_position=OBJECT)]),
                        ('key', key)],
                ),
            )
            for u, v, key, data in graph.edges(keys=True, data=True)
        ],
    }
