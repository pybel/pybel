# -*- coding: utf-8 -*-

from collections import defaultdict

from ..utils import hash_edge


def stratify_hash_edges(graph):
    """Splits all qualified and unqualified edges by different indexing strategies

    :param BELGraph graph: A BEL network
    :rtype dict[tuple, dict[int, int]], dict[tuple, dict[int, set[int]]]
    """
    qualified_edges = defaultdict(dict)
    unqualified_edges = defaultdict(lambda: defaultdict(set))

    for u, v, k, d in graph.edges_iter(keys=True, data=True):
        hashed_data = hash_edge(u, v, k, d)

        if k < 0:
            unqualified_edges[u, v][k].add(hashed_data)
        else:
            qualified_edges[u, v][hashed_data] = k

    return dict(qualified_edges), dict(unqualified_edges)
