# -*- coding: utf-8 -*-

"""Functions for inducing random sub-graphs."""

import bisect
import logging
import random
from operator import itemgetter

from ..utils import remove_isolated_nodes
from ...pipeline import transformation
from ...utils import update_metadata, update_node_helper

__all__ = [
    'get_graph_with_random_edges',
    'get_random_node',
    'get_random_subgraph',
]

log = logging.getLogger(__name__)


def _random_edge_iterator(graph, n_edges):
    """Get a random set of edges from the graph and randomly samples a key from each.

    :type graph: pybel.BELGraph
    :param int n_edges: Number of edges to randomly select from the given graph
    :rtype: iter[tuple[tuple,tuple,int,dict]]
    """
    universe_edges = list(graph.edges())
    random.shuffle(universe_edges)

    for u, v in universe_edges[:n_edges]:
        keys = list(graph[u][v])
        k = random.choice(keys)
        yield u, v, k, graph[u][v][k]


@transformation
def get_graph_with_random_edges(graph, n_edges):
    """Build a new graph from a seeding of edges.

    :type graph: pybel.BELGraph
    :param int n_edges: Number of edges to randomly select from the given graph
    :rtype: pybel.BELGraph
    """
    result = graph.fresh_copy()
    result.add_edges_from(_random_edge_iterator(graph, n_edges))

    update_metadata(graph, result)
    update_node_helper(graph, result)
    return result


#: How many edges should be sampled from a graph that's still reasonable to display
SAMPLE_RANDOM_EDGE_COUNT = 250
#: How many edges should be sampled as "seed" edges
SAMPLE_RANDOM_EDGE_SEED_COUNT = 5


class WeightedRandomGenerator(object):
    """A weighted random number generator.

    Adapted from: https://eli.thegreenplace.net/2010/01/22/weighted-random-generation-in-python
    """

    def __init__(self, values, weights):
        """Build a weighted random generator.

        :param Any values: A sequence corresponding to the weights
        :param weights: Weights for each. Should all be positive, but not necessarily normalized.
        """
        self.values = values
        self.totals = []
        weight_total = 0

        for weight in weights:
            weight_total += weight
            self.totals.append(weight_total)

    @property
    def total(self):
        """Get the total weight stored."""
        return self.totals[-1]

    def next_index(self):
        """Get a random index.

        :rtype: int
        """
        return bisect.bisect_right(self.totals, random.random() * self.total)

    def next(self):
        """Get a random value.

        :rtype: Any
        """
        return self.values[self.next_index()]


def get_random_node(graph, node_blacklist, invert_degrees=None):
    """Choose a node from the graph with probabilities based on their degrees.

    :type graph: networkx.Graph
    :param set[tuple] node_blacklist: Nodes to filter out
    :param Optional[bool] invert_degrees: Should the degrees be inverted? Defaults to true.
    :rtype: Optional[tuple]
    """
    try:
        nodes, degrees = zip(*(
            (node, degree)
            for node, degree in sorted(graph.degree(), key=itemgetter(1))
            if node not in node_blacklist
        ))
    except ValueError:  # something wrong with graph, probably no elements in graph.degree_iter
        return

    if invert_degrees is None or invert_degrees:
        # More likely to choose low degree nodes to explore, so don't make hubs
        degrees = [1 / degree for degree in degrees]

    wrg = WeightedRandomGenerator(nodes, degrees)
    return wrg.next()


def _helper(result, graph, number_edges_remaining, no_grow, invert_degrees=None):
    """Help build a random graph.

    :type result: networkx.Graph
    :type graph: networkx.Graph
    :type number_edges_remaining: int
    :type no_grow: set
    :type invert_degrees: Optional[bool]
    """
    original_node_count = graph.number_of_nodes()

    log.debug('adding remaining %d edges', number_edges_remaining)
    for _ in range(number_edges_remaining):

        source, possible_step_nodes, c = None, set(), 0
        while not source or not possible_step_nodes:
            source = get_random_node(result, no_grow, invert_degrees=invert_degrees)

            c += 1
            if c >= original_node_count:
                log.warning('infinite loop happening')
                log.warning('source: %s', source)
                log.warning('no grow: %s', no_grow)
                return  # Happens when after exhausting the connected components. Try increasing the number seed edges

            if source is None:
                continue  # maybe do something else?

            # Only keep targets in the original graph that aren't in the result graph
            possible_step_nodes = set(graph[source]) - set(result[source])

            if not possible_step_nodes:
                no_grow.add(source)  # there aren't any possible nodes to step to, so try growing from somewhere else

        step_node = random.choice(list(possible_step_nodes))

        # it's not really a big deal which, but it might be possible to weight this by the utility of edges later
        key, attr_dict = random.choice(list(graph[source][step_node].items()))

        result.add_edge(source, step_node, key=key, **attr_dict)


@transformation
def get_random_subgraph(graph, number_edges=None, number_seed_edges=None, seed=None, invert_degrees=None):
    """Generate a random subgraph based on weighted random walks from random seed edges.

    :type graph: pybel.BELGraph graph
    :param Optional[int] number_edges: Maximum number of edges. Defaults to
     :data:`pybel_tools.constants.SAMPLE_RANDOM_EDGE_COUNT` (250).
    :param Optional[int] number_seed_edges: Number of nodes to start with (which likely results in different components
     in large graphs). Defaults to :data:`SAMPLE_RANDOM_EDGE_SEED_COUNT` (5).
    :param Optional[int] seed: A seed for the random state
    :param Optional[bool] invert_degrees: Should the degrees be inverted? Defaults to true.
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

    log.debug('getting random sub-graph with %d seed edges, %d final edges, and seed=%s', number_seed_edges,
              number_edges, seed)

    # Get initial graph with `number_seed_edges` edges
    result = get_graph_with_random_edges(graph, number_seed_edges)

    number_edges_remaining = number_edges - result.number_of_edges()
    _helper(
        result,
        graph,
        number_edges_remaining,
        no_grow=set(),  # This is the set of nodes that should no longer be chosen to grow from
        invert_degrees=invert_degrees,
    )

    log.debug('removing isolated nodes')
    remove_isolated_nodes(result)

    # update metadata
    update_node_helper(graph, result)
    update_metadata(graph, result)

    return result
