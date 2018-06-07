# -*- coding: utf-8 -*-

"""Functions for building node predicates."""

from collections import Iterable

from six import string_types

from ...constants import FUNCTION

__all__ = [
    'function_inclusion_filter_builder',
]


def _single_function_inclusion_filter_builder(func):
    def function_inclusion_filter(graph, node):
        """Passes only for a node that has the enclosed function

        :param BELGraph graph: A BEL Graph
        :param tuple node: A BEL node
        :return: If the node doesn't have the enclosed function
        :rtype: bool
        """
        return graph.node[node][FUNCTION] == func

    return function_inclusion_filter


def _collection_function_inclusion_builder(funcs):
    funcs = set(funcs)

    def functions_inclusion_filter(graph, node):
        """Passes only for a node that is one of the enclosed functions

        :param BELGraph graph: A BEL Graph
        :param tuple node: A BEL node
        :return: If the node doesn't have the enclosed functions
        :rtype: bool
        """
        return graph.node[node][FUNCTION] in funcs

    return functions_inclusion_filter


def function_inclusion_filter_builder(func):
    """Build a filter that only passes on nodes of the given function(s).

    :param func: A BEL Function or list/set/tuple of BEL functions
    :type func: str or iter[str]
    :return: A node filter (graph, node) -> bool
    :rtype: (pybel.BELGraph, tuple) -> bool
    """
    if isinstance(func, string_types):
        return _single_function_inclusion_filter_builder(func)

    elif isinstance(func, Iterable):
        return _collection_function_inclusion_builder(func)

    raise ValueError('Invalid type for argument: {}'.format(func))
