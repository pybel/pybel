# -*- coding: utf-8 -*-


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
