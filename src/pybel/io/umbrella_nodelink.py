# -*- coding: utf-8 -*-

"""Conversion functions for customized node-link JSON format prior canonicalization.

As an alternative to previous JSON
export functions, PyBEL also provides a customized JSON exporter prior node canonicalization. This module uses the
:mod:`pybel.canonicalize` module prior exporting to the node-link JSON format. This allows the inclusion of modifiers
in the nodes instead of the edges, the default schema in PyBEL.
"""

import json
from itertools import chain, count
from typing import Any, Mapping, TextIO, Union

from networkx.utils import open_file

from ..canonicalize import _decanonicalize_edge_node, edge_to_tuple
from ..constants import GRAPH_ANNOTATION_LIST, OBJECT, SUBJECT
from ..struct import BELGraph

__all__ = [
    'to_umbrella_nodelink',
    'to_umbrella_nodelink_file',
]


def to_umbrella_nodelink(graph: BELGraph) -> Mapping[str, Any]:
    """Convert this graph to a node-link JSON object by previously canonicalizing the nodes.

    :param graph: A BEL graph
    """
    """Convert a customized node-link format prior canonicalization.

        The canonicalization enables to incorporate additional information in the nodes such as modifiers that is present in
        the edges in PyBEL.

        :param graph: BEL Graph
        """
    nodes = set()

    for u, v, data in graph.edges(data=True):
        u_key, _, v_key = edge_to_tuple(u, v, data)
        nodes.add(u_key)
        nodes.add(v_key)

    nodes = sorted(list(nodes))
    mapping = dict(zip(nodes, count()))

    graph_json_dict = {
        'directed': True,
        'multigraph': True,
        'graph': graph.graph.copy(),
        'nodes': nodes,
        'links': [
            dict(
                chain(
                    data.copy().items(),
                    [
                        ('source', mapping[_decanonicalize_edge_node(u, data, node_position=SUBJECT)]),
                        ('target', mapping[_decanonicalize_edge_node(v, data, node_position=OBJECT)]),
                        ('key', key),
                    ],
                ),
            )
            for u, v, key, data in graph.edges(keys=True, data=True)
        ],
    }

    # Convert annotation list definitions (which are sets) to canonicalized/sorted lists
    graph_json_dict['graph'][GRAPH_ANNOTATION_LIST] = {
        keyword: list(sorted(values))
        for keyword, values in graph_json_dict['graph'].get(GRAPH_ANNOTATION_LIST, {}).items()
    }

    return graph_json_dict


@open_file(1, mode='w')
def to_umbrella_nodelink_file(graph: BELGraph, path: Union[str, TextIO], **kwargs) -> None:
    """Write this graph as node-link JSON to a file.

    :param graph: A BEL graph
    :param path: A path or file-like
    """
    graph_json_dict = to_umbrella_nodelink(graph)
    json.dump(graph_json_dict, path, ensure_ascii=False, **kwargs)
