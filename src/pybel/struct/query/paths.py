# -*- coding: utf-8 -*-

import itertools as itt

import networkx as nx

from ...constants import FUNCTION, PATHOLOGY

__all__ = [
    'get_nodes_in_all_shortest_paths',
]


def _get_nodes_in_all_shortest_paths_helper(graph, nodes, weight=None, remove_pathologies=True):
    if remove_pathologies:
        graph = graph.copy()
        for node, data in graph.nodes(data=True):
            if data[FUNCTION] == PATHOLOGY:
                graph.remove_node(node)

    for u, v in itt.product(nodes, repeat=2):
        try:
            yield from nx.all_shortest_paths(graph, u, v, weight=weight)
        except nx.exception.NetworkXNoPath:
            continue


def get_nodes_in_all_shortest_paths(graph, nodes, weight=None, remove_pathologies=False):
    """Gets all shortest paths from all nodes to all other nodes in the given list and returns the set of all nodes
    contained in those paths using :func:`networkx.all_shortest_paths`.

    :param pybel.BELGraph graph: A BEL graph
    :param iter[tuple] nodes: The list of nodes to use to use to find all shortest paths
    :param str weight: Edge data key corresponding to the edge weight. If none, uses unweighted search.
    :param bool remove_pathologies: Should pathology nodes be removed first?
    :return: A set of nodes appearing in the shortest paths between nodes in the BEL graph
    :rtype: set[tuple]

    .. note:: This can be trivially parallelized using :func:`networkx.single_source_shortest_path`
    """
    shortest_paths_nodes_iterator = _get_nodes_in_all_shortest_paths_helper(graph, nodes, weight=weight,
                                                                            remove_pathologies=remove_pathologies)

    return set(itt.chain.from_iterable(shortest_paths_nodes_iterator))
