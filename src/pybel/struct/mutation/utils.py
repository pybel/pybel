# -*- coding: utf-8 -*-

"""General-use induction functions."""

import networkx as nx

from ..filters import filter_edges
from ..filters.typing import EdgePredicates
from ..pipeline import in_place_transformation, transformation, uni_in_place_transformation
from ..utils import update_metadata, update_node_helper

__all__ = [
    'remove_isolated_nodes',
    'remove_isolated_nodes_op',
    'expand_by_edge_filter',
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
def expand_by_edge_filter(source, target, edge_predicates: EdgePredicates):
    """Expand a target graph by edges in the source matching the given predicates.

    :param pybel.BELGraph source: A BEL graph
    :param pybel.BELGraph target: A BEL graph
    :param edge_predicates: An edge predicate or list of edge predicates
    :return: A BEL sub-graph induced over the edges passing the given filters
    :rtype: pybel.BELGraph
    """
    target.add_edges_from(
        (u, v, k, source[u][v][k])
        for u, v, k in filter_edges(source, edge_predicates=edge_predicates)
    )

    update_node_helper(source, target)
    update_metadata(source, target)
    # TODO smarter ways of ensuring metadata
