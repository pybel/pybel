# -*- coding: utf-8 -*-

from ..utils import expand_by_edge_filter
from ...filters import build_downstream_edge_predicate, build_upstream_edge_predicate
from ...pipeline import uni_in_place_transformation

__all__ = [
    'expand_upstream_causal',
    'expand_downstream_causal',
]


@uni_in_place_transformation
def expand_upstream_causal(universe, graph):
    """Add the upstream causal relations to the given sub-graph.

    :param pybel.BELGraph universe: A BEL graph representing the universe of all knowledge
    :param pybel.BELGraph graph: The target BEL graph to enrich with upstream causal controllers of contained nodes
    """
    expand_by_edge_filter(universe, graph, build_upstream_edge_predicate(graph))


@uni_in_place_transformation
def expand_downstream_causal(universe, graph):
    """Add the downstream causal relations to the given sub-graph.

    :param pybel.BELGraph universe: A BEL graph representing the universe of all knowledge
    :param pybel.BELGraph graph: The target BEL graph to enrich with upstream causal controllers of contained nodes
    """
    expand_by_edge_filter(universe, graph, build_downstream_edge_predicate(graph))
