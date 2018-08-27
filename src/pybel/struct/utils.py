# -*- coding: utf-8 -*-

import networkx as nx

__all__ = [
    'update_metadata',
    'update_node_helper',
    'ensure_node_from_universe',
    'relabel_inplace',
]


def update_metadata(source, target):
    """Update the namespace and annotation metadata in the target graph.

    :param pybel.BELGraph source:
    :param pybel.BELGraph target:
    """
    target.namespace_url.update(source.namespace_url)
    target.namespace_pattern.update(source.namespace_pattern)

    target.annotation_url.update(source.annotation_url)
    target.annotation_pattern.update(source.annotation_pattern)

    for keyword, values in source.annotation_list.items():
        if keyword not in target.annotation_list:
            target.annotation_list[keyword] = values
        else:
            for value in values:
                target.annotation_list[keyword].add(value)


def update_node_helper(source, target):
    """Update the nodes' data dictionaries in the target graph from the source graph.

    :param nx.Graph source: The universe of all knowledge
    :param nx.Graph target: The target BEL graph
    """
    for node in target:
        if node not in source:
            continue
        target._node[node] = source._node[node]


def ensure_node_from_universe(source, target, node):
    """Ensure the target graph has the given node using data from the source graph.

    :param pybel.BELGraph source: The universe of all knowledge
    :param pybel.BELGraph target: The target BEL graph
    :param tuple node: A BEL node
    """
    if node not in target:
        target.add_node(node)
        target._node[node] = source._node[node]


def relabel_inplace(G, mapping):  # borrowed from NX
    old_labels = set(mapping.keys())
    new_labels = set(mapping.values())
    if len(old_labels & new_labels) > 0:
        # labels sets overlap
        # can we topological sort and still do the relabeling?
        D = nx.DiGraph(list(mapping.items()))
        D.remove_edges_from(nx.selfloop_edges(D))
        try:
            nodes = reversed(list(nx.topological_sort(D)))
        except nx.NetworkXUnfeasible:
            raise nx.NetworkXUnfeasible('The node label sets are overlapping '
                                        'and no ordering can resolve the '
                                        'mapping. Use copy=True.')
    else:
        # non-overlapping label sets
        nodes = old_labels

    for old in nodes:
        try:
            new = mapping[old]
        except KeyError:
            continue
        if new == old:
            continue
        try:
            G.add_node(new)
            G._node[new] = G.nodes[old]  # THIS WAS CHANGED
        except KeyError:
            raise KeyError("Node %s is not in the graph" % old)
        new_edges = [(new, new if old == target else target, key, data)
                     for (_, target, key, data)
                     in G.edges(old, data=True, keys=True)]
        new_edges += [(new if old == source else source, new, key, data)
                      for (source, _, key, data)
                      in G.in_edges(old, data=True, keys=True)]
        G.remove_node(old)
        G.add_edges_from(new_edges)
    return G
