# -*- coding: utf-8 -*-

"""Functions for summarizing the errors logged during BEL parsing and compilation."""

from collections import Counter

from ...parser.exc import NakedNameWarning

__all__ = [
    'get_syntax_errors',
    'count_error_types',
    'count_naked_names',
    'get_naked_names',
]


def get_syntax_errors(graph):
    """Gets a list of the syntax errors from the BEL script underlying the graph. Uses SyntaxError as a
    stand-in for :exc:`pybel.parser.parse_exceptions.BelSyntaxError`

    :param pybel.BELGraph graph: A BEL graph
    :return: A list of 4-tuples of line number, line text, exception, and annotations present in the parser
    :rtype: list[tuple]
    """
    return [
        (number, line, exc, an)
        for number, line, exc, an in graph.warnings
        if isinstance(exc, SyntaxError)
    ]


def count_error_types(graph):
    """Count the occurrence of each type of error in a graph.

    :param pybel.BELGraph graph: A BEL graph
    :return: A Counter of {error type: frequency}
    :rtype: collections.Counter
    """
    return Counter(e.__class__.__name__ for _, _, e, _ in graph.warnings)


def _naked_names_iter(graph):
    """Iterate over naked name warnings from a graph.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: iter[NakedNameWarning]
    """
    for _, _, e, _ in graph.warnings:
        if isinstance(e, NakedNameWarning):
            yield e.name


def count_naked_names(graph):
    """Count the frequency of each naked name (names without namespaces).

    :param pybel.BELGraph graph: A BEL graph
    :return: A Counter from {name: frequency}
    :rtype: collections.Counter
    """
    return Counter(_naked_names_iter(graph))


def get_naked_names(graph):
    """Get the set of naked names in the graph.

    :param pybel.BELGraph graph: A BEL graph
    :rtype: set[str]
    """
    return set(_naked_names_iter(graph))
