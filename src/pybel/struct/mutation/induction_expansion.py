# -*- coding: utf-8 -*-

"""Functions for building graphs that use both expansion and induction procedures."""

import logging
from typing import Iterable, Union

from .expansion import expand_all_node_neighborhoods
from .expansion.upstream import expand_downstream_causal, expand_upstream_causal
from .induction.neighborhood import get_subgraph_by_neighborhood
from .induction.upstream import get_downstream_causal_subgraph, get_upstream_causal_subgraph
from ..pipeline import transformation
from ...dsl import BaseEntity

__all__ = [
    'get_multi_causal_upstream',
    'get_multi_causal_downstream',
    'get_subgraph_by_second_neighbors',
]

log = logging.getLogger(__name__)


@transformation
def get_multi_causal_upstream(graph, nbunch: Union[BaseEntity, Iterable[BaseEntity]]):
    """Get the union of all the 2-level deep causal upstream subgraphs from the nbunch.

    :param pybel.BELGraph graph: A BEL graph
    :param nbunch: A BEL node or list of BEL nodes
    :return: A subgraph of the original BEL graph
    :rtype: pybel.BELGraph
    """
    result = get_upstream_causal_subgraph(graph, nbunch)
    expand_upstream_causal(graph, result)
    return result


@transformation
def get_multi_causal_downstream(graph, nbunch: Union[BaseEntity, Iterable[BaseEntity]]):
    """Get the union of all of the 2-level deep causal downstream subgraphs from the nbunch.

    :param pybel.BELGraph graph: A BEL graph
    :param nbunch: A BEL node or list of BEL nodes
    :return: A subgraph of the original BEL graph
    :rtype: pybel.BELGraph
    """
    result = get_downstream_causal_subgraph(graph, nbunch)
    expand_downstream_causal(graph, result)
    return result


@transformation
def get_subgraph_by_second_neighbors(graph, nodes: Iterable[BaseEntity], filter_pathologies: bool = False):
    """Get a graph around the neighborhoods of the given nodes and expand to the neighborhood of those nodes.

    Returns none if none of the nodes are in the graph.

    :param pybel.BELGraph graph: A BEL graph
    :param nodes: An iterable of BEL nodes
    :param filter_pathologies: Should expansion take place around pathologies?
    :return: A BEL graph induced around the neighborhoods of the given nodes
    :rtype: Optional[pybel.BELGraph]
    """
    result = get_subgraph_by_neighborhood(graph, nodes)

    if result is None:
        return

    expand_all_node_neighborhoods(graph, result, filter_pathologies=filter_pathologies)
    return result
