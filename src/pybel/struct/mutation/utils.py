# -*- coding: utf-8 -*-

import networkx as nx

from ..pipeline import in_place_transformation, transformation

__all__ = [
    'remove_isolated_nodes',
    'remove_isolated_nodes_op',
]


@in_place_transformation
def remove_isolated_nodes(graph):
    """Remove isolated nodes from the network, in place.

    :param pybel.BELGraph graph: A BEL graph
    """
    nodes = list(nx.isolates(graph))
    graph.remove_nodes_from(nodes)


@transformation
def remove_isolated_nodes_op(graph):
    """Build a new graph excluding the isolated nodes.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: pybel.BELGraph
    """
    rv = graph.copy()
    nodes = list(nx.isolates(rv))
    rv.remove_nodes_from(nodes)
    return rv
