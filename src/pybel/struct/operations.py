# -*- coding: utf-8 -*-

import networkx as nx

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
        g.add_node(node, **h.node[node])


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


def left_full_join(g, h):
    """Adds all nodes and edges from ``h`` to ``g``, in-place for ``g``

    :param BELGraph g: A BEL network
    :param BELGraph h: A BEL network

    Example usage:

    >>> import pybel
    >>> g = pybel.from_path('...')
    >>> h = pybel.from_path('...')
    >>> merged = left_full_join(g, h)
    """
    _left_full_node_join(g, h)
    _left_full_metadata_join(g, h)

    for u, v, key, data in h.edges_iter(keys=True, data=True):
        if u not in g or v not in g[u] or key not in g[u][v]:
            g.add_edge(u, v, key=key, **data)


def left_outer_join(g, h):
    """Only adds components from the ``h`` that are touching ``g``.

    Algorithm:

    1. Identify all weakly connected components in ``h``
    2. Add those that have an intersection with the ``g``

    :param BELGraph g: A BEL network
    :param BELGraph h: A BEL network

    Example usage:

    >>> import pybel
    >>> g = pybel.from_path('...')
    >>> h = pybel.from_path('...')
    >>> merged = left_outer_join(g, h)
    """
    g_nodes = set(g)
    for comp in nx.weakly_connected_components(h):
        if g_nodes.intersection(comp):
            left_full_join(g, h.subgraph(comp))


def _left_full_join_networks(target, networks):
    """Full joins a list of networks to a target network

    The order of the networks will not impact the result.

    :param BELGraph target: A BEL network
    :param iter[BELGraph] networks: An iterator of BEL networks
    :rtype: BELGraph
    """
    for network in networks:
        left_full_join(target, network)
    return target


def _left_outer_join_networks(target, networks):
    """Outer joins a list of networks to a target network.

    Note: the order of networks will have significant results!

    :param BELGraph target: A BEL network
    :param iter[BELGraph] networks: An iterator of BEL networks
    :rtype: BELGraph
    """
    for network in networks:
        left_outer_join(target, network)
    return target


def union(networks):
    """Takes the union over a collection of networks into a new network. Assumes iterator is longer than 2, but not
    infinite.

    :param iter[BELGraph] networks: An iterator over BEL networks. Can't be infinite.
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

    return _left_full_join_networks(target, networks[1:])


def left_node_intersection_join(g, h):
    """Takes the intersection over two networks. This intersection of two graphs is defined by the
     union of the subgraphs induced over the intersection of their nodes

    :param BELGraph g: A BEL network
    :param BELGraph h: A BEL network
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

    left_full_join(g_inter, h_inter)

    return g_inter


def node_intersection(networks):
    """Takes the node intersection over a collection of networks into a new network. This intersection is defined
    the same way as by :func:`left_node_intersection_join`

    :param iter[BELGraph] networks: An iterable of networks. Since it's iterated over twice, it gets converted to a
                                    tuple first, so this isn't a safe operation for infinite lists.
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

    return union(subgraphs)
