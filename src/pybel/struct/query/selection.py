# -*- coding: utf-8 -*-

import itertools as itt

import logging
import networkx as nx

from .constants import *
from .induction import get_multi_causal_downstream, get_multi_causal_upstream
from .random_subgraph import get_random_subgraph
from ..filters import filter_nodes, is_causal_relation
from ..filters.node_predicate_builders import build_node_name_search
from ..mutation.expansion import expand_all_node_neighborhoods, expand_nodes_neighborhoods
from ..mutation.induction import get_subgraph_by_edge_filter, get_subgraph_by_induction
from ..mutation.induction.annotations import get_subgraph_by_annotations
from ..mutation.induction.citation import get_subgraph_by_authors, get_subgraph_by_pubmed
from ..mutation.induction.paths import get_subgraph_by_all_shortest_paths
from ..pipeline import transformation
from ..utils import update_metadata, update_node_helper

log = logging.getLogger(__name__)

__all__ = [
    'get_subgraph',
]


def search_node_names(graph, query):
    """Search for nodes containing a given string(s).

    :param pybel.BELGraph graph: A BEL graph
    :param query: The search query
    :type query: str or iter[str]
    :return: An iterator over nodes whose names match the search query
    :rtype: iter

    Example:

    .. code-block:: python

        >>> from pybel.examples import sialic_acid_graph
        >>> list(search_node_names(sialic_acid_graph, 'CD33'))
        [('Protein', 'HGNC', 'CD33'), ('Protein', 'HGNC', 'CD33', ('pmod', ('bel', 'Ph')))]
    """
    return filter_nodes(graph, build_node_name_search(query))


@transformation
def get_subgraph_by_node_filter(graph, node_filters):
    """Induces a graph on the nodes that pass all filters

    :param pybel.BELGraph graph: A BEL graph
    :param node_filters: A node filter or list/tuple of node filters
    :type node_filters: types.FunctionType or iter[types.FunctionType]
    :return: A subgraph induced over the nodes passing the given filters
    :rtype: pybel.BELGraph
    """
    return get_subgraph_by_induction(graph, filter_nodes(graph, node_filters))


@transformation
def get_subgraph_by_neighborhood(graph, nodes):
    """Gets a BEL graph around the neighborhoods of the given nodes. Returns none if no nodes are in the graph

    :param pybel.BELGraph graph: A BEL graph
    :param iter[tuple] nodes: An iterable of BEL nodes
    :return: A BEL graph induced around the neighborhoods of the given nodes
    :rtype: Optional[pybel.BELGraph]
    """
    rv = graph.fresh_copy()

    node_set = set(nodes)

    if all(node not in graph for node in node_set):
        return

    rv.add_edges_from(
        (
            (u, v, k, d)
            if k < 0 else
            (u, v, d)
        )
        for u, v, k, d in itt.chain(
            graph.in_edges_iter(nodes, keys=True, data=True),
            graph.out_edges_iter(nodes, keys=True, data=True)
        )
    )

    update_node_helper(graph, rv)
    update_metadata(graph, rv)

    return rv


@transformation
def get_subgraph_by_second_neighbors(graph, nodes, filter_pathologies=False):
    """Gets a BEL graph around the neighborhoods of the given nodes, and expands to the neighborhood of those nodes

    :param pybel.BELGraph graph: A BEL graph
    :param iter[tuple] nodes: An iterable of BEL nodes
    :param bool filter_pathologies: Should expansion take place around pathologies?
    :return: A BEL graph induced around the neighborhoods of the given nodes
    :rtype: Optional[pybel.BELGraph]
    """
    result = get_subgraph_by_neighborhood(graph, nodes)

    if result is None:
        return

    expand_all_node_neighborhoods(graph, result, filter_pathologies=filter_pathologies)
    return result


@transformation
def get_causal_subgraph(graph):
    """Builds a new subgraph induced over all edges that are causal

    :param pybel.BELGraph graph: A BEL graph
    :return: A subgraph of the original BEL graph
    :rtype: pybel.BELGraph
    """
    return get_subgraph_by_edge_filter(graph, is_causal_relation)


@transformation
def get_subgraph_by_node_search(graph, query):
    """Gets a subgraph induced over all nodes matching the query string

    :param pybel.BELGraph graph: A BEL Graph
    :param str or iter[str] query: A query string or iterable of query strings for node names
    :return: A subgraph induced over the original BEL graph
    :rtype: pybel.BELGraph

    Thinly wraps :func:`search_node_names` and :func:`get_subgraph_by_induction`.
    """
    nodes = search_node_names(graph, query)
    return get_subgraph_by_induction(graph, nodes)


@transformation
def get_subgraph(graph, seed_method=None, seed_data=None, expand_nodes=None, remove_nodes=None):
    """Runs pipeline query on graph with multiple subgraph filters and expanders.

    Order of Operations:

    1. Seeding by given function name and data
    2. Add nodes
    3. Remove nodes

    :param pybel.BELGraph graph: A BEL graph
    :param str seed_method: The name of the get_subgraph_by_* function to use
    :param seed_data: The argument to pass to the get_subgraph function
    :param list[tuple] expand_nodes: Add the neighborhoods around all of these nodes
    :param list[tuple] remove_nodes: Remove these nodes and all of their in/out edges
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

    elif not seed_method:  # Otherwise, don't seed a subgraph
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


@transformation
def get_largest_component(graph):
    """Gets the giant component of a subgraph

    :param pybel.BELGraph graph: A BEL Graph
    :return: The giant component of the graph
    :rtype: pybel.BELGraph
    """
    return max(nx.weakly_connected_component_subgraphs(graph), key=len)
