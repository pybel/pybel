# -*- coding: utf-8 -*-

"""Operations for BEL graphs."""

from typing import Iterable

import networkx as nx
from tqdm import tqdm

from .utils import update_metadata, update_node_helper
from ..dsl import BaseEntity

__all__ = [
    'subgraph',
    'left_full_join',
    'left_outer_join',
    'union',
    'left_node_intersection_join',
    'node_intersection',
]


def subgraph(graph, nodes: Iterable[BaseEntity]):
    """Induce a sub-graph over the given nodes.

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


def left_full_join(g, h) -> None:
    """Add all nodes and edges from ``h`` to ``g``, in-place for ``g``.

    :param pybel.BELGraph g: A BEL graph
    :param pybel.BELGraph h: A BEL graph

    Example usage:

    >>> import pybel
    >>> g = pybel.from_path('...')
    >>> h = pybel.from_path('...')
    >>> left_full_join(g, h)
    """
    g.add_nodes_from(
        (node, data)
        for node, data in h.nodes(data=True)
        if node not in g
    )
    g.add_edges_from(
        (u, v, key, data)
        for u, v, key, data in h.edges(keys=True, data=True)
        if u not in g or v not in g[u] or key not in g[u][v]
    )

    update_metadata(h, g)
    update_node_helper(h, g)
    g.warnings.extend(h.warnings)


def left_outer_join(g, h) -> None:
    """Only add components from the ``h`` that are touching ``g``.

    Algorithm:

    1. Identify all weakly connected components in ``h``
    2. Add those that have an intersection with the ``g``

    :param BELGraph g: A BEL graph
    :param BELGraph h: A BEL graph

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


def _left_outer_join_graphs(target, graphs):
    """Outer join a list of graphs to a target graph.

    Note: the order of graphs will have significant results!

    :param BELGraph target: A BEL graph
    :param iter[BELGraph] graphs: An iterator of BEL graphs
    :rtype: BELGraph
    """
    for graph in graphs:
        left_outer_join(target, graph)
    return target


def union(graphs, use_tqdm: bool = False):
    """Take the union over a collection of graphs into a new graph.

    Assumes iterator is longer than 2, but not infinite.

    :param iter[BELGraph] graphs: An iterator over BEL graphs. Can't be infinite.
    :param use_tqdm: Should a progress bar be displayed?
    :return: A merged graph
    :rtype: BELGraph

    Example usage:

    >>> import pybel
    >>> g = pybel.from_path('...')
    >>> h = pybel.from_path('...')
    >>> k = pybel.from_path('...')
    >>> merged = union([g, h, k])
    """
    it = iter(graphs)

    if use_tqdm:
        it = tqdm(it, desc='taking union')

    try:
        target = next(it)
    except StopIteration as e:
        raise ValueError('no graphs given') from e

    try:
        graph = next(it)
    except StopIteration:
        return target
    else:
        target = target.copy()
        left_full_join(target, graph)

    for graph in it:
        left_full_join(target, graph)

    return target


def left_node_intersection_join(g, h):
    """Take the intersection over two graphs.

    This intersection of two graphs is defined by the union of the sub-graphs induced over the intersection of their nodes

    :param BELGraph g: A BEL graph
    :param BELGraph h: A BEL graph
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


def node_intersection(graphs):
    """Take the node intersection over a collection of graphs into a new graph.

    This intersection is defined the same way as by :func:`left_node_intersection_join`

    :param iter[BELGraph] graphs: An iterable of graphs. Since it's iterated over twice, it gets converted to a
     tuple first, so this isn't a safe operation for infinite lists.
    :rtype: BELGraph

    Example usage:

    >>> import pybel
    >>> g = pybel.from_path('...')
    >>> h = pybel.from_path('...')
    >>> k = pybel.from_path('...')
    >>> merged = node_intersection([g, h, k])
    """
    graphs = tuple(graphs)

    n_graphs = len(graphs)

    if n_graphs == 0:
        raise ValueError('no graphs given')

    if n_graphs == 1:
        return graphs[0]

    nodes = set(graphs[0].nodes())

    for graph in graphs[1:]:
        nodes.intersection_update(graph)

    return union(
        subgraph(graph, nodes)
        for graph in graphs
    )
