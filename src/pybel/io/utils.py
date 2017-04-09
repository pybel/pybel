# -*- coding: utf-8 -*-

"""This module contains helper functions for other IO functions."""

from .io_exceptions import ImportVersionWarning
from ..utils import tokenize_version

#: The last PyBEL version where the graph data definition changed
PYBEL_MINIMUM_IMPORT_VERSION = (0, 4, 1)


def raise_for_old_graph(graph):
    graph_version = tokenize_version(graph.pybel_version)
    if graph_version < PYBEL_MINIMUM_IMPORT_VERSION:
        raise ImportVersionWarning(graph_version, PYBEL_MINIMUM_IMPORT_VERSION)


def ensure_version(graph, check_version=True):
    """Ensure that the graph was produced by a minimum of PyBEL v:data:`PYBEL_MINIMUM_IMPORT_VERSION`, which was the 
    last release with a change in the graph data definition.

    :param graph: A BEL Graph
    :type graph: BELGraph
    :param check_version: Should the version be checked, or should the graph just be returned without inspection
    :type check_version: bool
    """
    if check_version:
        raise_for_old_graph(graph)

    return graph
