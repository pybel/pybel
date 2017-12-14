# -*- coding: utf-8 -*-

from ...constants import KIND, PMOD, VARIANTS

__all__ = [
    'keep_node_permissive',
    'node_has_pmod',
    'node_data_has_pmod',
]

def keep_node_permissive(graph, node):
    """A default node filter that always evaluates to :data:`True`.

    Given BEL graph :code:`graph`, applying :func:`keep_node_permissive` with a filter on the nodes iterable
    as in :code:`filter(keep_node_permissive, graph.nodes_iter())` will result in the same iterable as
    :meth:`BELGraph.nodes_iter`

    :param BELGraph graph: A BEL graph
    :param tuple node: The node
    :return: Always returns :data:`True`
    :rtype: bool
    """
    return True


def node_has_pmod(graph, node):
    """

    :param BELGraph graph: A BEL graph
    :param tuple node: The node
    :rtype: bool
    """
    return node_data_has_pmod(graph.node[node])


def node_data_has_pmod(data):
    """Returns true if the data has a pmod

    :param dict data:
    :rtype: bool
    """
    if VARIANTS not in data:
        return False

    return any(
        variant[KIND] == PMOD
        for variant in data[VARIANTS]
    )
