# -*- coding: utf-8 -*-

"""This module contains helper functions for other IO functions."""

from .io_exceptions import ImportVersionWarning
from ..struct import BELGraph
from ..utils import tokenize_version

#: The last PyBEL version where the graph data definition changed
PYBEL_MINIMUM_IMPORT_VERSION = (0, 5, 11)


def raise_for_old_graph(graph):
    """Raises an ImportVersionWarning if the BEL graph was produced by a legacy version of PyBEL"""
    graph_version = tokenize_version(graph.pybel_version)
    if graph_version < PYBEL_MINIMUM_IMPORT_VERSION:
        raise ImportVersionWarning(graph_version, PYBEL_MINIMUM_IMPORT_VERSION)


def raise_for_not_bel(graph):
    """Raises a TypeError if the argument is not a BEL graph"""
    if not isinstance(graph, BELGraph):
        raise TypeError('Not a BELGraph: {}'.format(graph))


def ensure_version(graph, check_version=True):
    """Ensure that the graph was produced by a minimum of PyBEL v:data:`PYBEL_MINIMUM_IMPORT_VERSION`, which was the 
    last release with a change in the graph data definition.

    :param BELGraph graph: A BEL Graph
    :param bool check_version: Should the version be checked, or should the graph just be returned without inspection
    """
    if check_version:
        raise_for_old_graph(graph)

    return graph
