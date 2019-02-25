# -*- coding: utf-8 -*-

"""A wrapper around selection methods."""

import logging
from typing import Any, List, Optional

from .constants import (
    SEED_TYPE_ANNOTATION, SEED_TYPE_AUTHOR, SEED_TYPE_DOUBLE_NEIGHBORS, SEED_TYPE_DOWNSTREAM,
    SEED_TYPE_INDUCTION, SEED_TYPE_NEIGHBORS, SEED_TYPE_PATHS, SEED_TYPE_PUBMED, SEED_TYPE_SAMPLE, SEED_TYPE_UPSTREAM,
)
from ..mutation import (
    expand_nodes_neighborhoods, get_multi_causal_downstream, get_multi_causal_upstream,
    get_random_subgraph, get_subgraph_by_all_shortest_paths, get_subgraph_by_annotations, get_subgraph_by_authors,
    get_subgraph_by_induction, get_subgraph_by_neighborhood, get_subgraph_by_pubmed, get_subgraph_by_second_neighbors,
)
from ...dsl import BaseEntity

log = logging.getLogger(__name__)

__all__ = [
    'get_subgraph',
]


def get_subgraph(graph,
                 seed_method: Optional[str] = None,
                 seed_data: Optional[Any] = None,
                 expand_nodes: Optional[List[BaseEntity]] = None,
                 remove_nodes: Optional[List[BaseEntity]] = None,
                 ):
    """Run a pipeline query on graph with multiple sub-graph filters and expanders.

    Order of Operations:

    1. Seeding by given function name and data
    2. Add nodes
    3. Remove nodes

    :param pybel.BELGraph graph: A BEL graph
    :param seed_method: The name of the get_subgraph_by_* function to use
    :param seed_data: The argument to pass to the get_subgraph function
    :param expand_nodes: Add the neighborhoods around all of these nodes
    :param remove_nodes: Remove these nodes and all of their in/out edges
    :rtype: Optional[pybel.BELGraph]
    """
    # Seed by the given function
    if seed_method == SEED_TYPE_INDUCTION:
        result = get_subgraph_by_induction(graph, seed_data)

    elif seed_method == SEED_TYPE_PATHS:
        result = get_subgraph_by_all_shortest_paths(graph, seed_data)

    elif seed_method == SEED_TYPE_NEIGHBORS:
        result = get_subgraph_by_neighborhood(graph, seed_data)

    elif seed_method == SEED_TYPE_DOUBLE_NEIGHBORS:
        result = get_subgraph_by_second_neighbors(graph, seed_data)

    elif seed_method == SEED_TYPE_UPSTREAM:
        result = get_multi_causal_upstream(graph, seed_data)

    elif seed_method == SEED_TYPE_DOWNSTREAM:
        result = get_multi_causal_downstream(graph, seed_data)

    elif seed_method == SEED_TYPE_PUBMED:
        result = get_subgraph_by_pubmed(graph, seed_data)

    elif seed_method == SEED_TYPE_AUTHOR:
        result = get_subgraph_by_authors(graph, seed_data)

    elif seed_method == SEED_TYPE_ANNOTATION:
        result = get_subgraph_by_annotations(graph, seed_data['annotations'], or_=seed_data.get('or'))

    elif seed_method == SEED_TYPE_SAMPLE:
        result = get_random_subgraph(
            graph,
            number_edges=seed_data.get('number_edges'),
            seed=seed_data.get('seed')
        )

    elif not seed_method:  # Otherwise, don't seed a sub-graph
        result = graph.copy()
        log.debug('no seed function - using full network: %s', result.name)

    else:
        raise ValueError('Invalid seed method: {}'.format(seed_method))

    if result is None:
        log.debug('query returned no results')
        return

    log.debug('original graph has (%s nodes / %s edges)', result.number_of_nodes(), result.number_of_edges())

    # Expand around the given nodes
    if expand_nodes:
        expand_nodes_neighborhoods(graph, result, expand_nodes)
        log.debug('graph expanded to (%s nodes / %s edges)', result.number_of_nodes(), result.number_of_edges())

    # Delete the given nodes
    if remove_nodes:
        for node in remove_nodes:
            if node not in result:
                log.debug('%s is not in graph %s', node, graph.name)
                continue
            result.remove_node(node)
        log.debug('graph contracted to (%s nodes / %s edges)', result.number_of_nodes(), result.number_of_edges())

    log.debug(
        'Subgraph coming from %s (seed type) %s (data) contains %d nodes and %d edges',
        seed_method,
        seed_data,
        result.number_of_nodes(),
        result.number_of_edges()
    )

    return result
