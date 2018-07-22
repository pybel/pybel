# -*- coding: utf-8 -*-

"""Functions for inducing random sub-graphs."""

from random import choice, shuffle

__all__ = [
    'get_graph_with_random_edges',
]


def _random_edge_iterator(graph, n_edges):
    """Get a random set of edges from the graph and randomly samples a key from each.

    :type graph: pybel.BELGraph
    :param int n_edges: Number of edges to randomly select from the given graph
    :rtype: iter[tuple[tuple,tuple,int,dict]]
    """
    universe_edges = graph.edges()
    shuffle(universe_edges)

    for u, v in universe_edges[:n_edges]:
        keys = list(graph[u][v])
        k = choice(keys)
        yield u, v, k, graph[u][v][k]


def get_graph_with_random_edges(graph, n_edges):
    """Build a new graph from a seeding of edges.

    :type graph: pybel.BELGraph
    :param int n_edges: Number of edges to randomly select from the given graph
    :rtype: pybel.BELGraph
    """
    result = graph.fresh_copy()

    result.add_edges_from(
        (
            (u, v, k, d)
            if k < 0 else
            (u, v, d)
        )
        for u, v, k, d in _random_edge_iterator(graph, n_edges)
    )

    return result
