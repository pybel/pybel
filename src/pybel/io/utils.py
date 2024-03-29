# -*- coding: utf-8 -*-

"""This module contains helper functions for other IO functions."""

from .exc import ImportVersionWarning
from ..config import PYBEL_MINIMUM_IMPORT_VERSION
from ..struct import BELGraph
from ..utils import tokenize_version


def raise_for_old_graph(graph):
    """Raise an ImportVersionWarning if the BEL graph was produced by a legacy version of PyBEL.

    :param graph: A BEL graph
    :raises ImportVersionWarning: If the BEL graph was produced by a legacy version of PyBEL
    """
    graph_version = tokenize_version(graph.pybel_version)
    if graph_version < PYBEL_MINIMUM_IMPORT_VERSION:
        raise ImportVersionWarning(graph_version, PYBEL_MINIMUM_IMPORT_VERSION)


def raise_for_not_bel(graph):
    """Raise a TypeError if the argument is not a BEL graph.

    :param graph: A BEL graph
    :raises TypeError: If the argument is not a BEL graph
    """
    if not isinstance(graph, BELGraph):
        raise TypeError("Not a BELGraph: {}".format(graph))


def ensure_version(graph: BELGraph, check_version: bool = True) -> BELGraph:
    """Ensure that the graph was produced by a minimum of PyBEL v:data:`PYBEL_MINIMUM_IMPORT_VERSION`.

    This variable is defined by last release with a change in the graph data definition.

    :param graph: A BEL Graph
    :param check_version: Should the version be checked, or should the graph just be returned without inspection
    :raises ImportVersionWarning: If the BEL graph was produced by a legacy version of PyBEL
    """
    if check_version:
        raise_for_old_graph(graph)

    return graph
