# -*- coding: utf-8 -*-

"""Conversion functions for BEL graphs with `GraphML <https://en.wikipedia.org/wiki/GraphML>`_."""

from typing import BinaryIO, Optional, Union

import networkx as nx

from ..canonicalize import edge_to_tuple
from ..constants import RELATION
from ..struct import BELGraph

__all__ = [
    'to_graphml',
]


def to_graphml(graph: BELGraph, path: Union[str, BinaryIO], schema: Optional[str] = None) -> None:
    """Write a graph to a GraphML XML file using :func:`networkx.write_graphml`.

    :param graph: BEL Graph
    :param path: Path to the new exported file
    :param schema: Type of export. Currently supported: "simple" and "umbrella".

    The .graphml file extension is suggested so Cytoscape can recognize it.
    By default, this function exports using the PyBEL schema of including modifier information into the edges.
    As an alternative, this function can also distinguish between
    """
    if schema is None or schema == 'simple':
        rv = _to_graphml_simple(graph)
    elif schema == 'umbrella':
        rv = _to_graphml_umbrella(graph)
    else:
        raise ValueError('Unhandled schema: {}'.format(schema))

    nx.write_graphml(rv, path)


def _to_graphml_simple(graph: BELGraph) -> nx.MultiDiGraph:
    """Convert a BEL graph to a simple graph.

    :param graph: A BEL graph
    """
    rv = nx.MultiDiGraph()

    for node in graph:
        rv.add_node(node.as_bel(), function=node.function)

    for u, v, key, edge_data in graph.edges(data=True, keys=True):
        u_key, v_key = u.as_bel(), v.as_bel()
        rv.add_edge(
            u_key,
            v_key,
            key=key,
            interaction=edge_data[RELATION],
            bel=graph.edge_to_bel(u, v, edge_data),
        )

    return rv


def _to_graphml_umbrella(graph: BELGraph) -> nx.MultiDiGraph:
    """Convert a BEL graph to a new graph the nodes as original BEL terms strings.

    :param graph: A BEL graph
    """
    rv = nx.MultiDiGraph()

    for u, v, key, edge_data in graph.edges(data=True, keys=True):
        u_key, _, v_key = edge_to_tuple(u, v, edge_data)

        rv.add_edge(
            u_key,
            v_key,
            key=key,
            relation=edge_data[RELATION],
            bel=graph.edge_to_bel(u, v, edge_data),
        )

    return rv
