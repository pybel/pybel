# -*- coding: utf-8 -*-

import logging

from ..mutation.expansion.upstream import expand_downstream_causal, expand_upstream_causal
from ..mutation.induction.upstream import get_downstream_causal_subgraph, get_upstream_causal_subgraph
from ..pipeline import transformation

__all__ = [
    'get_multi_causal_upstream',
    'get_multi_causal_downstream',
]

log = logging.getLogger(__name__)


@transformation
def get_multi_causal_upstream(graph, nbunch):
    """Get the union of all the 2-level deep causal upstream subgraphs from the nbunch.

    :param pybel.BELGraph graph: A BEL graph
    :param nbunch: A BEL node or list of BEL nodes
    :type nbunch: tuple or list[tuple]
    :return: A subgraph of the original BEL graph
    :rtype: pybel.BELGraph
    """
    result = get_upstream_causal_subgraph(graph, nbunch)
    expand_upstream_causal(graph, result)
    return result


@transformation
def get_multi_causal_downstream(graph, nbunch):
    """Get the union of all of the 2-level deep causal downstream subgraphs from the nbunch.

    :param pybel.BELGraph graph: A BEL graph
    :param nbunch: A BEL node or list of BEL nodes
    :type nbunch: tuple or list[tuple]
    :return: A subgraph of the original BEL graph
    :rtype: pybel.BELGraph
    """
    result = get_downstream_causal_subgraph(graph, nbunch)
    expand_downstream_causal(graph, result)
    return result
