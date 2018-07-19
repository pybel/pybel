# -*- coding: utf-8 -*-

import logging
import time
from random import choice, seed as seed_python_random

import numpy as np

from ..mutation.utils import remove_isolated_nodes
from ..pipeline import transformation
from ..utils import update_node_helper

__all__ = [
    'randomly_select_node',
    'get_random_subgraph',
]

log = logging.getLogger(__name__)

#: How many edges should be sampled from a graph that's still reasonable to display
SAMPLE_RANDOM_EDGE_COUNT = 250
#: How many edges should be sampled as "seed" edges
SAMPLE_RANDOM_EDGE_SEED_COUNT = 5


def randomly_select_node(graph, no_grow, random_state):
    """Chooses a node from the graph to expand upon

    :param pybel.BELGraph graph: The graph to filter from
    :param set[tuple] no_grow: Nodes to filter out
    :param random_state: The random state
    :rtype: Optional[tuple]
    """
    try:
        nodes, degrees = zip(*(
            (node, degree)
            for node, degree in graph.degree_iter()
            if node not in no_grow
        ))
    except ValueError:  # something wrong with graph, probably no elements in graph.degree_iter
        return

    ds = sum(degrees)

    if 0 == ds:
        log.warning('graph has no edges in it')
        log.warning('number nodes: %s', graph.number_of_nodes())
        raise ZeroDivisionError

    norm_inv_degrees = [d / ds for d in degrees]
    nci = random_state.choice(len(nodes), p=norm_inv_degrees)
    return nodes[nci]


def _get_number_topological_edges(graph):
    """Count the number of edges in the topology of the graph

    :param networkx.DiGraph graph:
    :rtype: int
    """
    return sum(
        len(graph[node])
        for node in graph
    )


def _will_sample_full_graph(graph, number_edges):
    """Returns true if this graph has fewer topological (connections between a given two nodes, regardless of its
    key and value) edges than the given number

    :param pybel.BELGraph graph:
    :param int number_edges: number edges to check
    :rtype: bool
    """
    return _get_number_topological_edges(graph) <= number_edges


def _get_random_u_v_k_triples(graph, number_seed_edges, random_state):
    """Gets a random set of edges from the graph and randomly samples a key from each

    :param pybel.BELGraph graph:
    :param int number_seed_edges:
    :rtype: iter[tuple[tuple,tuple,int]]
    """
    universe_edges = [
        (u, v)
        for u in graph
        for v in graph.edge[u]
    ]
    random_state.shuffle(universe_edges)

    for u, v in universe_edges[:number_seed_edges]:
        keys = list(graph[u][v])
        key = random_state.choice(keys)
        yield u, v, key


def _get_graph_with_random_edges(graph, number_seed_edges, random_state):
    """Builds a new graph from a seeding of edges

    :param graph:
    :param number_seed_edges:
    :param random_state:
    :return:
    """
    log.debug('making new graph with %d random edges', number_seed_edges)

    rv = graph.fresh_copy()

    for u, v, key in _get_random_u_v_k_triples(graph, number_seed_edges, random_state):
        rv.add_edge(u, v, key=key, attr_dict=graph[u][v][key])

    return rv


def _helper(rv, graph, number_edges_remaining, no_grow, random_state, original_node_count):
    t = time.time()
    t_fives = 0
    log.debug('adding remaining %d edges', number_edges_remaining)
    for i in range(number_edges_remaining):
        possible_step_nodes = None

        c = 0
        while not possible_step_nodes:
            source = randomly_select_node(rv, no_grow, random_state)

            c += 1
            if c >= original_node_count:
                log.warning('infinite loop happening')
                log.warning('source: %s', source)
                log.warning('no grow: %s', no_grow)
                return  # This happens when we've exhaused the connected components. Try increasing the number seed edges

            if source is None:
                continue  # maybe do something else?

            possible_step_nodes = set(graph.edge[source]) - set(rv.edge[source])

            if not possible_step_nodes:
                no_grow.add(source)  # there aren't any possible nodes to step to, so try growing from somewhere else

        step_node = choice(list(possible_step_nodes))

        # it's not really a big deal which, but it might be possible to weight this by the utility of edges later
        key, attr_dict = choice(list(graph.edge[source][step_node].items()))

        rv.add_edge(source, step_node, key=key, attr_dict=attr_dict)


@transformation
def get_random_subgraph(graph, number_edges=None, number_seed_edges=None, seed=None):
    """Randomly picks a node from the graph, and performs a weighted random walk to sample the given number of edges
    around it

    :param pybel.BELGraph graph:
    :param Optional[int] number_edges: Maximum number of edges. Defaults to
                                       :data:`pybel_tools.constants.SAMPLE_RANDOM_EDGE_COUNT` (250).
    :param Optional[int] number_seed_edges: Number of nodes to start with (which likely results in different components
                                            in large graphs). Defaults to :data:`SAMPLE_RANDOM_EDGE_SEED_COUNT`.
    :param Optional[int] seed: A seed for the random state
    :rtype: pybel.BELGraph
    """
    # Set default parameters
    number_edges = number_edges or SAMPLE_RANDOM_EDGE_COUNT
    number_seed_edges = number_seed_edges or SAMPLE_RANDOM_EDGE_SEED_COUNT
    random_state = np.random.RandomState(seed=seed)
    seed_python_random(seed)

    # Check if graph will sample full graph, and just return it if it would
    if _will_sample_full_graph(graph, number_edges):
        log.info('sampled full graph')
        return graph.copy()

    log.debug('getting random subgraph with %d seed edges, %d final edges, and seed=%s', number_seed_edges,
              number_edges, seed)

    original_node_count = graph.number_of_nodes()
    no_grow = set()  #: This is the set of nodes that should no longer be chosen to grow from

    # Get initial graph with `number_seed_edges` edges
    rv = _get_graph_with_random_edges(graph, number_seed_edges, random_state)

    number_edges_remaining = number_edges - number_seed_edges

    _helper(rv, graph, number_edges_remaining, no_grow, random_state, original_node_count)

    log.debug('removing isolated nodes')
    remove_isolated_nodes(rv)

    log.debug('updating metadata')
    update_node_helper(graph, rv)

    return rv
