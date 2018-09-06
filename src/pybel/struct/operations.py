# -*- coding: utf-8 -*-

import networkx as nx

from .utils import update_metadata, update_node_helper

__all__ = [
    'subgraph',
    'left_full_join',
    'left_outer_join',
    'union',
    'left_node_intersection_join',
    'node_intersection',
]


def subgraph(graph, nodes):
    """Induce a sub-graph over the given nodes.

    :param BELGraph graph:
    :param set[BaseEntity] nodes:
    :rtype: BELGraph
    """
    sg = graph.subgraph(nodes)

    # see implementation for .copy()
    result = graph.fresh_copy()
    result.graph.update(sg.graph)

    for node, data in sg.nodes(data=True):
        result.add_node(node, **data)

    result.add_edges_from(
        (u, v, key, datadict.copy())
        for u, v, key, datadict in sg.edges(keys=True, data=True)
    )

    return result


def left_full_join(g, h):
    """Add all nodes and edges from ``h`` to ``g``, in-place for ``g``

    :param pybel.BELGraph g: A BEL network
    :param pybel.BELGraph h: A BEL network

    Example usage:

    >>> import pybel
    >>> g = pybel.from_path('...')
    >>> h = pybel.from_path('...')
    >>> left_full_join(g, h)
    """
    g.add_edges_from(
        (u, v, key, data)
        for u, v, key, data in h.edges(keys=True, data=True)
        if u not in g or v not in g[u] or key not in g[u][v]
    )

    update_metadata(h, g)
    update_node_helper(h, g)


def left_outer_join(g, h):
    """Only add components from the ``h`` that are touching ``g``.

    Algorithm:

    1. Identify all weakly connected components in ``h``
    2. Add those that have an intersection with the ``g``

    :param BELGraph g: A BEL network
    :param BELGraph h: A BEL network

    Example usage:

    >>> import pybel
    >>> g = pybel.from_path('...')
    >>> h = pybel.from_path('...')
    >>> left_outer_join(g, h)
    """
    g_nodes = set(g)
    for comp in nx.weakly_connected_components(h):
        if g_nodes.intersection(comp):
            h_subgraph = subgraph(h, comp)
            left_full_join(g, h_subgraph)


def _left_outer_join_networks(target, networks):
    """Outer join a list of networks to a target network.

    Note: the order of networks will have significant results!

    :param BELGraph target: A BEL network
    :param iter[BELGraph] networks: An iterator of BEL networks
    :rtype: BELGraph
    """
    for network in networks:
        left_outer_join(target, network)
    return target


def union(networks):
    """Take the union over a collection of networks into a new network. Assumes iterator is longer than 2, but not
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

    for network in networks[1:]:
        left_full_join(target, network)

    return target


def left_node_intersection_join(g, h):
    """Take the intersection over two networks. This intersection of two graphs is defined by the
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

    g_inter = subgraph(g, intersecting)
    h_inter = subgraph(h, intersecting)

    left_full_join(g_inter, h_inter)

    return g_inter


def node_intersection(networks):
    """Take the node intersection over a collection of networks into a new network. This intersection is defined
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

    nodes = set(networks[0].nodes())

    for network in networks[1:]:
        nodes.intersection_update(network)

    return union(
        subgraph(network, nodes)
        for network in networks
    )
