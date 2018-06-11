# -*- coding: utf-8 -*-

import logging

from ...pipeline import transformation
from ....constants import CAUSAL_RELATIONS, RELATION

__all__ = [
    'get_upstream_causal_subgraph',
]

log = logging.getLogger(__name__)


@transformation
def get_upstream_causal_subgraph(graph, nbunch):
    """Induce a subgraph from all of the upstream causal entities of the nodes in the nbunch.

    :param pybel.BELGraph graph: A BEL graph
    :param nbunch: A BEL node or iterable of BEL nodes
    :type nbunch: tuple or iter[tuple]
    :rtype: pybel.BELGraph
    """
    rv = graph.fresh_copy()

    rv.add_edges_from(
        (u, v, key, data)
        for u, v, key, data in graph.in_edges(nbunch, keys=True, data=True)
        if data[RELATION] in CAUSAL_RELATIONS
    )
    return rv
