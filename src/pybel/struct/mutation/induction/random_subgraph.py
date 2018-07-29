# -*- coding: utf-8 -*-

"""Functions for inducing random sub-graphs."""

import bisect
import logging
import random
from operator import itemgetter

from ..utils import remove_isolated_nodes, update_metadata, update_node_helper
from ...pipeline import transformation

__all__ = [
    'get_graph_with_random_edges',
    'get_random_node',
    'get_random_subgraph',
]

log = logging.getLogger(__name__)

#: How many edges should be sampled from a graph that's still reasonable to display
SAMPLE_RANDOM_EDGE_COUNT = 250
#: How many edges should be sampled as "seed" edges
SAMPLE_RANDOM_EDGE_SEED_COUNT = 5


def _random_edge_iterator(graph, n_edges):
    """Get a random set of edges from the graph and randomly samples a key from each.

    :type graph: pybel.BELGraph
    :param int n_edges: Number of edges to randomly select from the given graph
    :rtype: iter[tuple[tuple,tuple,int,dict]]
    """
    universe_edges = graph.edges()
    random.shuffle(universe_edges)

    for u, v in universe_edges[:n_edges]:
        keys = list(graph[u][v])
        k = random.choice(keys)
        yield u, v, k, graph[u][v][k]


def get_graph_with_random_edges(graph, n_edges):
    """Build a new graph from a seeding of edges.

    :type graph: pybel.BELGraph
    :param int n_edges: Number of edges to randomly select from the given graph
    :rtype: pybel.BELGraph
    """
    result = graph.fresh_copy()

    result.add_edges_from(
        (
            (u, v, k, d)
            if k < 0 else
            (u, v, d)
        )
        for u, v, k, d in _random_edge_iterator(graph, n_edges)
    )

    return result


class WeightedRandomGenerator(object):
    """A weighted random number generator."""

    def __init__(self, weights):
        self.totals = []
        weight_total = 0

        for weight in weights:
            weight_total += weight
            self.totals.append(weight_total)

    def next(self):
        """Get a random index."""
        rnd = random.random() * self.totals[-1]
        return bisect.bisect_right(self.totals, rnd)


def get_random_node(graph, node_blacklist):
    """Choose a node from the graph with probabilities based on their degrees.

    :type graph: networkx.Graph
    :param set[tuple] node_blacklist: Nodes to filter out
    :rtype: Optional[tuple]
    """
    try:
        nodes, degrees = zip(*(
            (node, degree)
            for node, degree in sorted(graph.degree_iter(), key=itemgetter(1))
            if node not in node_blacklist
        ))
    except ValueError:  # something wrong with graph, probably no elements in graph.degree_iter
        return

    wrg = WeightedRandomGenerator(degrees)
    index = wrg.next()
    return nodes[index]


def _helper(rv, graph, number_edges_remaining, no_grow, original_node_count):
    log.debug('adding remaining %d edges', number_edges_remaining)
    for i in range(number_edges_remaining):
        possible_step_nodes = None

        c = 0
        while not possible_step_nodes:
            source = get_random_node(rv, no_grow)

            c += 1
            if c >= original_node_count:
                log.warning('infinite loop happening')
                log.warning('source: %s', source)
                log.warning('no grow: %s', no_grow)
                return  # This happens when we've exhaused the connected components. Try increasing the number seed edges

            if source is None:
                continue  # maybe do something else?

            possible_step_nodes = set(graph[source]) - set(rv[source])

            if not possible_step_nodes:
                no_grow.add(source)  # there aren't any possible nodes to step to, so try growing from somewhere else

        step_node = random.choice(list(possible_step_nodes))

        # it's not really a big deal which, but it might be possible to weight this by the utility of edges later
        key, attr_dict = random.choice(list(graph[source][step_node].items()))

        rv.add_edge(source, step_node, key=key, **attr_dict)


@transformation
def get_random_subgraph(graph, number_edges=None, number_seed_edges=None, seed=None):
    """Randomly picks a node from the graph, and performs a weighted random walk to sample the given number of edges
    around it

    :type graph: pybel.BELGraph graph
    :param Optional[int] number_edges: Maximum number of edges. Defaults to
     :data:`pybel_tools.constants.SAMPLE_RANDOM_EDGE_COUNT` (250).
    :param Optional[int] number_seed_edges: Number of nodes to start with (which likely results in different components
     in large graphs). Defaults to :data:`SAMPLE_RANDOM_EDGE_SEED_COUNT` (5).
    :param Optional[int] seed: A seed for the random state
    :rtype: pybel.BELGraph
    """
    if number_edges is None:
        number_edges = SAMPLE_RANDOM_EDGE_COUNT

    if number_seed_edges is None:
        number_seed_edges = SAMPLE_RANDOM_EDGE_SEED_COUNT

    if seed is not None:
        random.seed(seed)

    # Check if graph will sample full graph, and just return it if it would
    if graph.number_of_edges() <= number_edges:
        log.info('sampled full graph')
        return graph.copy()

    log.debug('getting random subgraph with %d seed edges, %d final edges, and seed=%s', number_seed_edges,
              number_edges, seed)

    original_node_count = graph.number_of_nodes()
    no_grow = set()  #: This is the set of nodes that should no longer be chosen to grow from

    # Get initial graph with `number_seed_edges` edges
    rv = get_graph_with_random_edges(graph, number_seed_edges)

    number_edges_remaining = number_edges - number_seed_edges

    _helper(rv, graph, number_edges_remaining, no_grow, original_node_count)

    log.debug('removing isolated nodes')
    remove_isolated_nodes(rv)

    log.debug('updating metadata')
    update_node_helper(graph, rv)
    update_metadata(graph, rv)

    return rv
