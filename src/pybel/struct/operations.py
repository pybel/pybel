# -*- coding: utf-8 -*-

import networkx as nx

from .utils import stratify_hash_edges

__all__ = [
    'left_full_join',
    'left_outer_join',
    'union',
    'left_node_intersection_join',
    'node_intersection',
]


def _left_full_node_join(g, h):
    """Adds all nodes from ``h`` to ``g``, in-place for ``g``

    :param BELGraph g: A BEL network
    :param BELGraph h: A BEL network
    """
    for node in h:
        if node in g:
            continue
        g.add_node(node, attr_dict=h.node[node])


def _left_full_metadata_join(g, h):
    """Adds all metadata from ``h`` to ``g``, in-place for ``g``

    :param pybel.BELGraph g: A BEL network
    :param pybel.BELGraph h: A BEL network
    """
    g.namespace_url.update(h.namespace_url)
    g.namespace_pattern.update(h.namespace_pattern)

    g.annotation_url.update(h.annotation_url)
    g.annotation_pattern.update(h.annotation_pattern)

    for keyword, values in h.annotation_list.items():
        if keyword not in g.annotation_list:
            g.annotation_list[keyword] = values
        else:
            for value in values:
                g.annotation_list[keyword].add(value)


def left_full_join(g, h, use_hash=True):
    """Adds all nodes and edges from ``h`` to ``g``, in-place for ``g``

    :param BELGraph g: A BEL network
    :param BELGraph h: A BEL network
    :param bool use_hash: If true, uses a hash join algorithm. Else, uses an exhaustive search, which takes much longer.

    Example usage:

    >>> import pybel
    >>> g = pybel.from_path('...')
    >>> h = pybel.from_path('...')
    >>> merged = left_full_join(g, h)
    """
    if use_hash:
        _left_full_hash_join(g, h)
    else:
        _left_full_exhaustive_join(g, h)


def _left_full_exhaustive_join(g, h):
    """Adds all nodes and edges from H to G, in-place for G using an exhaustive algorithm to ensure correctness,
    but runs in O(|E(G)| * |E(H)|)

    :param BELGraph g: A BEL network
    :param BELGraph h: A BEL network
    """
    _left_full_node_join(g, h)
    _left_full_metadata_join(g,h)

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


def _left_full_hash_join(g, h):
    """Adds all nodes and edges from H to G, in-place for G using a hash-based approach for faster speed. Runs
    in O(|E(G)| + |E(H)|)

    :param BELGraph g: A BEL network
    :param BELGraph h: A BEL network
    """
    _left_full_node_join(g, h)
    _left_full_metadata_join(g, h)

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


def left_outer_join(g, h, use_hash=True):
    """Only adds components from the ``h`` that are touching ``g``.

    Algorithm:

    1. Identify all weakly connected components in ``h``
    2. Add those that have an intersection with the ``g``

    :param BELGraph g: A BEL network
    :param BELGraph h: A BEL network
    :param bool use_hash: If true, uses a hash join algorithm. Else, uses an exhaustive search, which takes much longer.

    Example usage:

    >>> import pybel
    >>> g = pybel.from_path('...')
    >>> h = pybel.from_path('...')
    >>> merged = left_outer_join(g, h)
    """
    g_nodes = set(g)
    for comp in nx.weakly_connected_components(h):
        if g_nodes.intersection(comp):
            left_full_join(g, h.subgraph(comp), use_hash=use_hash)


def _left_full_join_networks(target, networks, use_hash=True):
    """Full joins a list of networks to a target network

    The order of the networks will not impact the result.

    :param BELGraph target: A BEL network
    :param iter[BELGraph] networks: An iterator of BEL networks
    :param bool use_hash: If true, uses a hash join algorithm. Else, uses an exhaustive search, which takes much longer.
    :rtype: BELGraph
    """
    for network in networks:
        left_full_join(target, network, use_hash=use_hash)
    return target


def _left_outer_join_networks(target, networks, use_hash=True):
    """Outer joins a list of networks to a target network.

    Note: the order of networks will have significant results!

    :param BELGraph target: A BEL network
    :param iter[BELGraph] networks: An iterator of BEL networks
    :param bool use_hash: If true, uses a hash join algorithm. Else, uses an exhaustive search, which takes much longer.
    :rtype: BELGraph
    """
    for network in networks:
        left_outer_join(target, network, use_hash=use_hash)
    return target


def union(networks, use_hash=True):
    """Takes the union over a collection of networks into a new network. Assumes iterator is longer than 2, but not
    infinite.

    :param iter[BELGraph] networks: An iterator over BEL networks. Can't be infinite.
    :param bool use_hash: If true, uses a hash join algorithm. Else, uses an exhaustive search, which takes much longer.
    :return: A merged network
    :rtype: BELGraph

    Example usage:

    >>> import pybel
    >>> g = pybel.from_path('...')
    >>> h = pybel.from_path('...')
    >>> k = pybel.from_path('...')
    >>> merged = union([g, h, k])
    """
    networks = tuple(networks)

    n_networks = len(networks)

    if n_networks == 0:
        raise ValueError('no networks given')

    if n_networks == 1:
        return networks[0]

    target = networks[0].copy()

    return _left_full_join_networks(target, networks[1:], use_hash=use_hash)


def left_node_intersection_join(g, h, use_hash=True):
    """Takes the intersection over two networks. This intersection of two graphs is defined by the
     union of the subgraphs induced over the intersection of their nodes

    :param BELGraph g: A BEL network
    :param BELGraph h: A BEL network
    :param bool use_hash: If true, uses a hash join algorithm. Else, uses an exhaustive search, which takes much longer.
    :rtype: BELGraph

    Example usage:

    >>> import pybel
    >>> g = pybel.from_path('...')
    >>> h = pybel.from_path('...')
    >>> merged = left_node_intersection_join(g, h)
    """
    intersecting = set(g).intersection(set(h))

    g_inter = g.subgraph(intersecting)
    h_inter = h.subgraph(intersecting)

    left_full_join(g_inter, h_inter, use_hash=use_hash)

    return g_inter


def node_intersection(networks, use_hash=True):
    """Takes the node intersection over a collection of networks into a new network. This intersection is defined
    the same way as by :func:`left_node_intersection_join`

    :param iter[BELGraph] networks: An iterable of networks. Since it's iterated over twice, it gets converted to a
                                    tuple first, so this isn't a safe operation for infinite lists.
    :param bool use_hash: If true, uses a hash join algorithm. Else, uses an exhaustive search, which takes much longer.
    :rtype: BELGraph

    Example usage:

    >>> import pybel
    >>> g = pybel.from_path('...')
    >>> h = pybel.from_path('...')
    >>> k = pybel.from_path('...')
    >>> merged = node_intersection([g, h, k])
    """
    networks = tuple(networks)

    n_networks = len(networks)

    if n_networks == 0:
        raise ValueError('no networks given')

    if n_networks == 1:
        return networks[0]

    nodes = set(networks[0])

    for network in networks[1:]:
        nodes.intersection_update(network)

    subgraphs = (
        network.subgraph(nodes)
        for network in networks
    )

    return union(subgraphs, use_hash=use_hash)
