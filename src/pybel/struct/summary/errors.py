# -*- coding: utf-8 -*-

"""Summary functions for errors and warnings encountered during the compilation of BEL script."""

from collections import Counter, defaultdict
from typing import Iterable, List, Mapping, Set

from ..filters.edge_predicates import edge_has_annotation
from ..graph import BELGraph, WarningTuple
from ...constants import ANNOTATIONS
from ...parser.exc import BELSyntaxError, MissingNamespaceNameWarning, MissingNamespaceRegexWarning, NakedNameWarning

__all__ = [
    'get_syntax_errors',
    'count_error_types',
    'count_naked_names',
    'get_naked_names',
    'calculate_incorrect_name_dict',
    'calculate_error_by_annotation',
]


def get_syntax_errors(graph: BELGraph) -> List[WarningTuple]:
    """List the syntax errors encountered during compilation of a BEL script."""
    return [
        (path, exc, an)
        for path, exc, an in graph.warnings
        if isinstance(exc, BELSyntaxError)
    ]


def count_error_types(graph: BELGraph) -> Counter:
    """Count the occurrence of each type of error in a graph.

    :return: A Counter of {error type: frequency}
    """
    return Counter(
        exc.__class__.__name__
        for _, exc, _ in graph.warnings
    )


def _naked_names_iter(graph: BELGraph) -> Iterable[str]:
    """Iterate over naked name warnings from a graph."""
    for _, exc, _ in graph.warnings:
        if isinstance(exc, NakedNameWarning):
            yield exc.name


def count_naked_names(graph: BELGraph) -> Counter:
    """Count the frequency of each naked name (names without namespaces).

    :return: A Counter from {name: frequency}
    """
    return Counter(_naked_names_iter(graph))


def get_naked_names(graph: BELGraph) -> Set[str]:
    """Get the set of naked names in the graph."""
    return set(_naked_names_iter(graph))


def _iterate_namespace_name(graph: BELGraph):
    for _, exc, _ in graph.warnings:
        if not isinstance(exc, (MissingNamespaceNameWarning, MissingNamespaceRegexWarning)):
            continue
        yield exc.namespace, exc.name


def calculate_incorrect_name_dict(graph: BELGraph) -> Mapping[str, List[str]]:
    """Get missing names grouped by namespace."""
    missing = defaultdict(list)

    for namespace, name in _iterate_namespace_name(graph):
        missing[namespace].append(name)

    return dict(missing)


def calculate_error_by_annotation(graph: BELGraph, annotation: str) -> Mapping[str, List[str]]:
    """Group error names by a given annotation."""
    results = defaultdict(list)

    for _, exc, ctx in graph.warnings:
        if not ctx or not edge_has_annotation(ctx, annotation):
            continue

        values = ctx[ANNOTATIONS][annotation]

        if isinstance(values, str):
            results[values].append(exc.__class__.__name__)

        elif isinstance(values, Iterable):
            for value in values:
                results[value].append(exc.__class__.__name__)

    return dict(results)
