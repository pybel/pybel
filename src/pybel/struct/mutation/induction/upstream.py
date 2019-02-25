# -*- coding: utf-8 -*-

"""Functions for inducing up/downstream causal subgraphs."""

import logging
from typing import Iterable, Union

from .utils import get_subgraph_by_edge_filter
from ...filters import build_downstream_edge_predicate, build_upstream_edge_predicate
from ...pipeline import transformation
from ....dsl import BaseEntity

__all__ = [
    'get_upstream_causal_subgraph',
    'get_downstream_causal_subgraph',
]

log = logging.getLogger(__name__)


@transformation
def get_upstream_causal_subgraph(graph, nbunch: Union[BaseEntity, Iterable[BaseEntity]]):
    """Induce a sub-graph from all of the upstream causal entities of the nodes in the nbunch.

    :type graph: pybel.BELGraph
    :rtype: pybel.BELGraph
    """
    return get_subgraph_by_edge_filter(graph, build_upstream_edge_predicate(nbunch))


@transformation
def get_downstream_causal_subgraph(graph, nbunch: Union[BaseEntity, Iterable[BaseEntity]]):
    """Induce a sub-graph from all of the downstream causal entities of the nodes in the nbunch.

    :type graph: pybel.BELGraph
    :rtype: pybel.BELGraph
    """
    return get_subgraph_by_edge_filter(graph, build_downstream_edge_predicate(nbunch))
