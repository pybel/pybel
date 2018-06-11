# -*- coding: utf-8 -*-

import networkx as nx

from ..pipeline import in_place_transformation, transformation, uni_in_place_transformation

__all__ = [
    'remove_isolated_nodes',
    'remove_isolated_nodes_op',
    'update_node_helper',
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


@uni_in_place_transformation
def update_node_helper(universe, graph):
    """Update the nodes' data dictionaries from the universe.

    :param nx.Graph universe: The universe of all knowledge
    :param nx.Graph graph: The target BEL graph
    """
    for node in graph:
        if node not in universe:
            continue
        graph.node[node].update(universe.node[node])
