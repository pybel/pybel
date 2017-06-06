# -*- coding: utf-8 -*-

from collections import defaultdict

import networkx as nx

__all__ = [
    'left_full_join',
    'left_outer_join',
]


def left_full_node_join(g, h):
    """Adds all nodes from H to G, in-place for G

    :param BELGraph g: A BEL Graph
    :param BELGraph h: A BEL Graph
    """
    for node in h.nodes_iter():
        if node not in g:
            g.add_node(node, attr_dict=h.node[node])


def left_full_join(g, h, use_hash=True):
    """Adds all nodes and edges from H to G, in-place for G

    :param BELGraph g: A BEL Graph
    :param BELGraph h: A BEL Graph
    :param bool use_hash: If true, uses a hash join algorithm. Else, uses an exhaustive search, which takes much longer.
    """
    if use_hash:
        return left_full_hash_join(g, h)
    else:
        return left_full_exhaustive_join(g, h)


def left_full_exhaustive_join(g, h):
    """Adds all nodes and edges from H to G, in-place for G

    :param BELGraph g: A BEL Graph
    :param BELGraph h: A BEL Graph
    """
    left_full_node_join(g, h)

    for u, v, k, d in h.edges_iter(keys=True, data=True):
        if k < 0:  # unqualified edge that's not in G yet
            if v not in g.edge[u] or k not in g.edge[u][v]:
                g.add_edge(u, v, key=k, attr_dict=d)
        elif v not in g.edge[u]:
            g.add_edge(u, v, attr_dict=d)
        elif any(0 <= gk and d == gd for gk, gd in g.edge[u][v].items()):
            continue
        else:
            g.add_edge(u, v, attr_dict=d)


def left_full_hash_join(g, h):
    """Adds all nodes and edges from H to G, in-place for G using a hash-based approach for faster speed.

    :param BELGraph g: A BEL Graph
    :param BELGraph h: A BEL Graph
    """
    left_full_node_join(g, h)

    g_qualified_edges, g_unqualified_edges = stratify_hash_edges(g)
    h_qualified_edges, h_unqualified_edges = stratify_hash_edges(h)

    # deal with unqualified edges
    for u, v in h_unqualified_edges:
        if (u, v) not in g_unqualified_edges:
            for k in h_unqualified_edges[u, v]:
                g.add_edge(u, v, key=k, attr_dict=h.edge[u][v][k])
        else:
            for k in h_unqualified_edges[u, v]:
                if k not in g.edge[u][v]:
                    g.add_edge(u, v, key=k, attr_dict=h.edge[u][v][k])

    for u, v in h_qualified_edges:
        if (u, v) not in g_qualified_edges:
            for attr_dict in h.edge[u][v].values():
                g.add_edge(u, v, attr_dict=attr_dict)
        else:
            for d_hash in h_qualified_edges[u, v]:
                if d_hash not in g_qualified_edges[u, v]:
                    g.add_edge(u, v, attr_dict=h.edge[u][v][h_qualified_edges[u, v][d_hash]])


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

    :param BELGraph graph: A BEL Graph
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


def left_outer_join(g, h, use_hash=True):
    """Only adds components from the right graph that are touching the left graph.

    1. Identify all weakly connected components in H
    2. Add those that have an intersection with the original graph

    :param BELGraph g: A BEL Graph
    :param BELGraph h: A BEL Graph
    :param bool use_hash: If true, uses a hash join algorithm. Else, uses an exhaustive search, which takes much longer.
    """
    g_nodes = set(g.nodes_iter())
    for comp in nx.weakly_connected_components(h):
        if g_nodes.intersection(comp):
            left_full_join(g, h.subgraph(comp), use_hash=use_hash)
