"""Functions for inducing up/downstream causal subgraphs."""

import logging
from collections.abc import Iterable

from .utils import get_subgraph_by_edge_filter
from ...filters.edge_predicate_builders import (
    build_downstream_edge_predicate,
    build_upstream_edge_predicate,
)
from ...pipeline import transformation
from ....dsl import BaseEntity

__all__ = [
    "get_downstream_causal_subgraph",
    "get_upstream_causal_subgraph",
]

logger = logging.getLogger(__name__)


@transformation
def get_upstream_causal_subgraph(graph, nbunch: BaseEntity | Iterable[BaseEntity]):
    """Induce a sub-graph from all upstream causal entities of the nodes in the nbunch."""
    return get_subgraph_by_edge_filter(graph, build_upstream_edge_predicate(nbunch))


@transformation
def get_downstream_causal_subgraph(graph, nbunch: BaseEntity | Iterable[BaseEntity]):
    """Induce a sub-graph from all downstream causal entities of the nodes in the nbunch."""
    return get_subgraph_by_edge_filter(graph, build_downstream_edge_predicate(nbunch))
