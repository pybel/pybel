# -*- coding: utf-8 -*-

"""Functions for summarizing the errors logged during BEL parsing and compilation."""

from collections import Counter, Iterable, defaultdict

from ..filters.edge_predicates import edge_has_annotation
from ...constants import ANNOTATIONS
from ...parser.exc import MissingNamespaceNameWarning, MissingNamespaceRegexWarning, NakedNameWarning

__all__ = [
    'get_syntax_errors',
    'count_error_types',
    'count_naked_names',
    'get_naked_names',
    'calculate_incorrect_name_dict',
    'calculate_error_by_annotation',
]


def get_syntax_errors(graph):
    """Gets a list of the syntax errors from the BEL script underlying the graph. Uses SyntaxError as a
    stand-in for :exc:`pybel.parser.exc.BelSyntaxError`

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


def _iterate_namespace_name(graph):
    for _, _, e, _ in graph.warnings:
        if not isinstance(e, (MissingNamespaceNameWarning, MissingNamespaceRegexWarning)):
            continue
        yield e.namespace, e.name


def calculate_incorrect_name_dict(graph):
    """Group all of the incorrect identifiers in a dict of {namespace: list of erroneous names}

    :param pybel.BELGraph graph: A BEL graph
    :return: A dictionary of {namespace: list of erroneous names}
    :rtype: dict[str, list[str]]
    """
    missing = defaultdict(list)

    for namespace, name in _iterate_namespace_name(graph):
        missing[namespace].append(name)

    return dict(missing)


def calculate_error_by_annotation(graph, annotation):
    """Group the graph by a given annotation and builds lists of errors for each.

    :param pybel.BELGraph graph: A BEL graph
    :param str annotation: The annotation to group errors by
    :return: A dictionary of {annotation value: list of errors}
    :rtype: dict[str, list[str]]
    """
    results = defaultdict(list)

    for _, _, e, context in graph.warnings:
        if not context or not edge_has_annotation(context, annotation):
            continue

        values = context[ANNOTATIONS][annotation]

        if isinstance(values, str):
            results[values].append(e.__class__.__name__)

        elif isinstance(values, Iterable):
            for value in values:
                results[value].append(e.__class__.__name__)

    return dict(results)
