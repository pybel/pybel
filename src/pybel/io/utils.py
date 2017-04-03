# -*- coding: utf-8 -*-

"""This module contains helper functions for other IO functions."""

from ..utils import tokenize_version


def ensure_version(graph, check_version=True):
    """Ensure that the graph was produced by a minimum of PyBEL v0.4.1, which was the last release with a change
    in the data structure

    :param graph: A BEL Graph
    :type graph: BELGraph
    :param check_version: Should the version be checked, or should the graph just be returned without inspection
    :type check_version: bool
    """
    minimum_version = (0, 4, 1)
    graph_version = tokenize_version(graph.pybel_version)
    if check_version and graph_version < minimum_version:
        raise ValueError('Tried importing from version {}. Need at least'.format(graph_version, minimum_version))
    return graph
