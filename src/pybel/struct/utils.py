# -*- coding: utf-8 -*-

from collections import defaultdict


def hash_dict(d):
    """Hashes a dictionary

    :param dict d: A dictionary to recursively hash
    :return: the hash value of the dictionary
    :rtype: int
    """
    h = 0
    for k, v in sorted(d.items()):
        h += hash(k)

        if isinstance(v, (set, list)):
            h += hash(tuple(sorted(v)))

        if isinstance(v, dict):
            h += hash_dict(v)

        if isinstance(v, (bool, int, tuple, str)):
            h += hash(v)

    return hash(h)


def stratify_hash_edges(graph):
    """Splits all qualified and unqualified edges by different indexing strategies

    :param BELGraph graph: A BEL network
    :rtype dict[tuple, dict[int, int]], dict[tuple, dict[int, set[int]]]
    """
    qualified_edges = defaultdict(dict)
    unqualified_edges = defaultdict(lambda: defaultdict(set))

    for u, v, k, d in graph.edges_iter(keys=True, data=True):
        hashed_data = hash_dict(d)

        if k < 0:
            unqualified_edges[u, v][k].add(hashed_data)
        else:
            qualified_edges[u, v][hashed_data] = k

    return dict(qualified_edges), dict(unqualified_edges)
