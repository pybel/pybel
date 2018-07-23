# -*- coding: utf-8 -*-

"""Induction methods for graphs over shortest paths."""

import itertools as itt

import logging
import networkx as nx

from .utils import get_subgraph_by_induction
from ...pipeline import transformation
from ....constants import FUNCTION, PATHOLOGY

__all__ = [
    'get_nodes_in_all_shortest_paths',
    'get_subgraph_by_all_shortest_paths',
]

log = logging.getLogger(__name__)


def _remove_pathologies_oop(graph):
    """Remove pathology nodes from the graph."""
    rv = graph.copy()
    for node, data in rv.nodes(data=True):
        if data[FUNCTION] == PATHOLOGY:
            rv.remove_node(node)
    return rv


def _iterate_nodes_in_shortest_paths(graph, nodes, weight=None):
    """Iterate over nodes in the shortest paths between all pairs of nodes in the given list.

    :type graph: pybel.BELGraph
    :type nodes: list[tuple]
    :param weight: Optional[str]
    :rtype: iter[tuple]
    """
    for source, target in itt.product(nodes, repeat=2):
        try:
            paths = nx.all_shortest_paths(graph, source, target, weight=weight)
            for path in paths:
                for node in path:
                    yield node
        except nx.exception.NetworkXNoPath:
            continue


def get_nodes_in_all_shortest_paths(graph, nodes, weight=None, remove_pathologies=False):
    """Get a set of nodes in all shortest paths between the given nodes.

    Thinly wraps :func:`networkx.all_shortest_paths`.

    :param pybel.BELGraph graph: A BEL graph
    :param iter[tuple] nodes: The list of nodes to use to use to find all shortest paths
    :param Optional[str] weight: Edge data key corresponding to the edge weight. If none, uses unweighted search.
    :param bool remove_pathologies: Should pathology nodes be removed first?
    :return: A set of nodes appearing in the shortest paths between nodes in the BEL graph
    :rtype: set[tuple]

    .. note:: This can be trivially parallelized using :func:`networkx.single_source_shortest_path`
    """
    if remove_pathologies:
        graph = _remove_pathologies_oop(graph)

    return set(_iterate_nodes_in_shortest_paths(graph, nodes, weight=weight))


@transformation
def get_subgraph_by_all_shortest_paths(graph, nodes, weight=None, remove_pathologies=False):
    """Induce a subgraph over the nodes in the pairwise shortest paths between all of the nodes in the given list.

    :param pybel.BELGraph graph: A BEL graph
    :param iter[tuple] nodes: A set of nodes over which to calculate shortest paths
    :param str weight: Edge data key corresponding to the edge weight. If None, performs unweighted search
    :param bool remove_pathologies: Should the pathology nodes be deleted before getting shortest paths?
    :return: A BEL graph induced over the nodes appearing in the shortest paths between the given nodes
    :rtype: Optional[pybel.BELGraph]
    """
    query_nodes = []

    for node in nodes:
        if node not in graph:
            log.debug('%s not in %s', node, graph)
            continue
        query_nodes.append(node)

    if not query_nodes:
        return

    induced_nodes = get_nodes_in_all_shortest_paths(graph, query_nodes, weight=weight,
                                                    remove_pathologies=remove_pathologies)

    if not induced_nodes:
        return

    return get_subgraph_by_induction(graph, induced_nodes)
