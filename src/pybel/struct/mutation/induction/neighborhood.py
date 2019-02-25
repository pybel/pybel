# -*- coding: utf-8 -*-

"""Functions for selecting by the neighborhoods of nodes."""

import itertools as itt
from typing import Iterable

from ...pipeline import transformation
from ...utils import update_metadata, update_node_helper
from ....dsl import BaseEntity

__all__ = [
    'get_subgraph_by_neighborhood',
]


@transformation
def get_subgraph_by_neighborhood(graph, nodes: Iterable[BaseEntity]):
    """Get a BEL graph around the neighborhoods of the given nodes.

    Returns none if no nodes are in the graph.

    :param pybel.BELGraph graph: A BEL graph
    :param nodes: An iterable of BEL nodes
    :return: A BEL graph induced around the neighborhoods of the given nodes
    :rtype: Optional[pybel.BELGraph]
    """
    node_set = set(nodes)

    if not any(node in graph for node in node_set):
        return

    rv = graph.fresh_copy()
    rv.add_edges_from(itt.chain(
        graph.in_edges(nodes, keys=True, data=True),
        graph.out_edges(nodes, keys=True, data=True),
    ))

    update_node_helper(graph, rv)
    update_metadata(graph, rv)

    return rv
