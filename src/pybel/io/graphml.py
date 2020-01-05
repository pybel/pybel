# -*- coding: utf-8 -*-

"""Conversion functions for BEL graphs with GraphML. More information at https://en.wikipedia.org/wiki/GraphML."""
from typing import BinaryIO, Optional, Union

import networkx as nx

from ..canonicalize import edge_to_tuple
from ..constants import RELATION
from ..struct import BELGraph

__all__ = [
    'to_graphml',
]


def to_graphml(graph: BELGraph, path: Union[str, BinaryIO], schema: Optional[str] = None) -> None:
    """Write this graph to GraphML XML file using :func:`networkx.write_graphml`.

    :param graph: BEL Graph
    :param path: Path to the new exported file
    :param schema: Type of export

    The .graphml file extension is suggested so Cytoscape can recognize it.
    By default, this function exports using the PyBEL schema of including modifier information into the edges.
    As an alternative, this function can also distinguish between
    """
    if schema is None or schema == 'simple':
        return _to_graphml_simple(graph, path)
    elif schema == 'belframework-counterintuitive':
        return _to_graphml_canonical(graph, path)
    else:
        raise ValueError('Unhandled schema: {}'.format(schema))


def _to_graphml_simple(graph: BELGraph, path: Union[str, BinaryIO]) -> None:
    """Convert a BEL graph to GraphML XML file using the PyBEL schema.

    :param graph: BEL Graph
    :param path: Path to the new exported file
    """
    rv = nx.MultiDiGraph()

    for node in graph:
        rv.add_node(node.as_bel(), function=node.function)

    for u, v, key, edge_data in graph.edges(data=True, keys=True):
        rv.add_edge(
            u.as_bel(),
            v.as_bel(),
            interaction=edge_data[RELATION],
            bel=graph.edge_to_bel(u, v, edge_data),
            key=key,
        )

    nx.write_graphml(rv, path)


def _to_graphml_canonical(graph: BELGraph, path: Union[str, BinaryIO]) -> None:
    """Convert a BEL graph to GraphML XML file by previously canonicalizing the nodes.

    :param graph: BEL Graph
    :param path: Path to the new exported file
    """
    rv = nx.MultiDiGraph()

    for u, v, key, data in graph.edges(data=True, keys=True):
        canonical_u, _, canonical_v = edge_to_tuple(u, v, data)

        rv.add_edge(
            canonical_u,
            canonical_v,
            key=key,
            **{
                'relation': data[RELATION],
                'bel': graph.edge_to_bel(u, v, data)
            }
        )

    nx.write_graphml(rv, path)
