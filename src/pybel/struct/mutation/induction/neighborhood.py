"""Functions for selecting by the neighborhoods of nodes."""

import itertools as itt
from collections.abc import Iterable

from ...graph import BELGraph
from ...pipeline import transformation
from ....dsl import BaseEntity

__all__ = [
    "get_subgraph_by_neighborhood",
]


@transformation
def get_subgraph_by_neighborhood(graph: BELGraph, nodes: Iterable[BaseEntity]) -> BELGraph | None:
    """Get a BEL graph around the neighborhoods of the given nodes.

    Returns none if no nodes are in the graph.

    :param graph: A BEL graph
    :param nodes: An iterable of BEL nodes
    :return: A BEL graph induced around the neighborhoods of the given nodes
    """
    node_set = set(nodes)

    if not any(node in graph for node in node_set):
        return

    rv = graph.child()
    rv.add_edges_from(
        itt.chain(
            graph.in_edges(nodes, keys=True, data=True),
            graph.out_edges(nodes, keys=True, data=True),
        ),
    )
    return rv
