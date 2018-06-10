# -*- coding: utf-8 -*-

import logging
import random
import time
from bisect import bisect

from ..utils import remove_isolated_nodes, update_node_helper
from ...pipeline import transformation

__all__ = [
    'get_random_subgraph',
]

log = logging.getLogger(__name__)

#: How many edges should be sampled from a graph that's still reasonable to display
SAMPLE_RANDOM_EDGE_COUNT = 250
#: How many edges should be sampled as "seed" edges
SAMPLE_RANDOM_EDGE_SEED_COUNT = 5


def weighted_choice(values, weights):
    """Make a weighted choice.

    From Raymond H: https://stackoverflow.com/a/4322940/5775947
    """
    total = 0
    cum_weights = []
    for w in weights:
        total += w
        cum_weights.append(total)
    x = random.random() * total
    i = bisect(cum_weights, x)
    return values[i]


def randomly_select_node(graph, no_grow):
    """Choose a node from the graph to expand upon.

    :param pybel.BELGraph graph: The graph to filter from
    :param set[tuple] no_grow: Nodes to filter out
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

    # use the normalized inverse degrees as weights
    weights = [d / ds for d in degrees]

    return weighted_choice(nodes, weights)

    # nci = random.choice(range(len(nodes)), p=norm_inv_degrees)
    # return nodes[nci]


def _get_number_topological_edges(graph):
    """Count the number of edges in the topology of the graph.

    :param networkx.DiGraph graph:
    :rtype: int
    """
    return sum(
        len(graph[node])
        for node in graph
    )


def _will_sample_full_graph(graph, number_edges):
    """Returns true if this graph has fewer topological (connections between a given two nodes, regardless of its
    key and value) edges than the given number.

    :param pybel.BELGraph graph: A BEL graph
    :param int number_edges: number edges to check
    :rtype: bool
    """
    return _get_number_topological_edges(graph) <= number_edges


def _get_random_u_v_k_triples(graph, number_seed_edges):
    """Get a random set of edges from the graph and randomly samples a key from each.

    :param pybel.BELGraph graph:
    :param number_seed_edges: Number of edges to randomly select from the given graph
    :rtype: iter[tuple[tuple,tuple,int]]
    """
    universe_edges = [
        (u, v)
        for u in graph
        for v in graph.edge[u]
    ]
    random.shuffle(universe_edges)

    for u, v in universe_edges[:number_seed_edges]:
        keys = list(graph[u][v])
        key = random.choice(keys)
        yield u, v, key


def _get_graph_with_random_edges(graph, number_seed_edges):
    """Build a new graph from a seeding of edges.

    :param pybel.BELGraph graph: A BEL graph
    :param number_seed_edges: Number of edges to randomly select from the given graph
    :rtype: pybel.BELGraph
    """
    result = graph.fresh_copy()

    result.add_edges_from(
        (u, v, key, graph[u][v][key])
        for u, v, key in _get_random_u_v_k_triples(graph, number_seed_edges)
    )

    return result


def _helper(rv, graph, number_edges_remaining, no_grow, original_node_count):
    t = time.time()
    t_fives = 0
    log.debug('adding remaining %d edges', number_edges_remaining)
    for i in range(number_edges_remaining):
        possible_step_nodes = None

        c = 0
        while not possible_step_nodes:
            source = randomly_select_node(rv, no_grow)

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

        step_node = random.choice(list(possible_step_nodes))

        # it's not really a big deal which, but it might be possible to weight this by the utility of edges later
        key, attr_dict = random.choice(list(graph.edge[source][step_node].items()))

        rv.add_edge(source, step_node, key=key, attr_dict=attr_dict)


@transformation
def get_random_subgraph(graph, number_edges=None, number_seed_edges=None, seed=None):
    """Generate a random subgraph with a nice topology for viewing.

    Randomly picks a node from the graph, and performs a weighted random walk to sample the given number of edges
    around it.

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
    random.seed(a=seed)

    # Check if graph will sample full graph, and just return it if it would
    if _will_sample_full_graph(graph, number_edges):
        log.info('sampled full graph. returning a copy.')
        return graph.copy()

    log.debug('getting random subgraph with %d seed edges, %d final edges, and seed=%s', number_seed_edges,
              number_edges, seed)

    original_node_count = graph.number_of_nodes()
    no_grow = set()  #: This is the set of nodes that should no longer be chosen to grow from

    # Get initial graph with `number_seed_edges` edges
    rv = _get_graph_with_random_edges(graph, number_seed_edges)

    number_edges_remaining = number_edges - number_seed_edges

    _helper(rv, graph, number_edges_remaining, no_grow, original_node_count)

    log.debug('removing isolated nodes')
    remove_isolated_nodes(rv)

    log.debug('updating metadata')
    update_node_helper(graph, rv)

    return rv
