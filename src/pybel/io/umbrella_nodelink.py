# -*- coding: utf-8 -*-

"""The Umbrella Node-Link JSON format is similar to node-link but uses full BEL terms as nodes.

Given a BEL statement describing that ``X`` phosphorylates ``Y`` like ``act(p(X)) -> p(Y, pmod(Ph))``,
PyBEL usually stores the ``act()`` information about ``X`` as part of the relationship. In Umbrella mode,
this stays as part of the node.

Note that this generates additional nodes in the network for each of the "modified" versions of
the node. For example, ``act(p(X))`` will be represented as individual node instead of
``p(X)``, as in the standard node-link JSON exporter.

A user might want to use this exporter in the following scenarios:

- Represent transitivity in activities like in ``p(X, pmod(Ph)) -> act(p(X)) -> p(Y, pmod(Ph)) -> act(p(Y))``
  with four nodes that are more ammenable to simulatons (e.g., boolean networks, petri nets).
- Visualizing networks that in similar way to the legacy BEL
  `Cytoscape plugin <https://apps.cytoscape.org/apps/belnavigator>`_ from the BEL Framework (warning: now defunct)
  using tools like Cytoscape.
"""

import gzip
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
    'to_umbrella_nodelink_gz',
]


def to_umbrella_nodelink(graph: BELGraph) -> Mapping[str, Any]:
    """Convert this graph to an umbrella node-link JSON object.

    :param graph: A BEL graph
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
    """Write this graph as an umbrella node-link JSON to a file.

    :param graph: A BEL graph
    :param path: A path or file-like
    """
    graph_json_dict = to_umbrella_nodelink(graph)
    json.dump(graph_json_dict, path, ensure_ascii=False, **kwargs)


def to_umbrella_nodelink_gz(graph, path: str, **kwargs) -> None:
    """Write this graph as an umbrella node-link JSON to a gzipped file."""
    with gzip.open(path, 'wt') as file:
        to_umbrella_nodelink_file(graph, file, **kwargs)
