# -*- coding: utf-8 -*-

"""Graph summary functions."""

import logging

import networkx as nx

log = logging.getLogger(__name__)


def summary_list(graph):
    """Return useful information about the graph as a list of tuples.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: list
    """
    number_nodes = graph.number_of_nodes()
    result = [
        ('nodes', number_nodes),
        ('edges', graph.number_of_edges()),
        ('network density', nx.density(graph)),
        ('components', nx.number_weakly_connected_components(graph)),
    ]

    try:
        result.append(('average degree', sum(graph.in_degree().values()) / float(number_nodes)))
    except ZeroDivisionError:
        log.info('%s has no nodes.', graph)

    if graph.warnings:
        result.append(('compilation warnings', len(graph.warnings)))

    return result


def summary_dict(graph):
    """Return useful information about the graph as a dictionary.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: dict
    """
    return dict(summary_list(graph))


def summary_str(graph):
    """Put useful information about the graph in a string.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: str
    """
    return '\n'.join(
        '{}: {}'.format(statistic.capitalize(), value)
        for statistic, value in summary_list(graph)
    )


def print_summary(graph, file=None):
    """Print useful information about the graph.

    :param pybel.BELGraph graph: A BEL graph
    :param file: A writeable file or file-like object. If None, defaults to :data:`sys.stdout`
    """
    print(summary_str(graph), file=file)
