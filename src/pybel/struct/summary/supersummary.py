# -*- coding: utf-8 -*-

"""Utilities for BEL graphs."""

import logging
import random
from collections import Counter
from typing import Optional, TextIO

import bioregistry
import pandas as pd
from humanize import intword
from tabulate import tabulate

from .node_summary import count_namespaces
from ..graph import BELGraph
from ...constants import CITATION, IDENTIFIER, NAMESPACE, RELATION, TWO_WAY_RELATIONS
from ...dsl import BaseConcept
from ...utils import multidict

logger = logging.getLogger(__name__)


def function_table_df(graph: BELGraph, examples: bool = True) -> pd.DataFrame:
    """Create a dataframe describing the functions in the graph."""
    function_mapping = multidict((node.function, node) for node in graph)
    function_c = Counter({function: len(nodes) for function, nodes in function_mapping.items()})
    if not examples:
        return pd.DataFrame(function_c.most_common(), columns=['Type', 'Count'])
    return pd.DataFrame(
        [
            (function, count, random.choice(function_mapping[function]))  # noqa:S311
            for function, count in function_c.most_common()
        ],
        columns=['Type', 'Count', 'Example'],
    )


def functions_str(graph, examples: bool = True, add_count: bool = True, **kwargs) -> str:
    """Make a summary string of the functions in the graph."""
    df = function_table_df(graph, examples=examples)
    headers = list(df.columns)
    if add_count:
        headers[0] += ' ({})'.format(len(df.index))
    return tabulate(df.values, headers=headers, **kwargs)


def functions(graph, file: Optional[TextIO] = None, examples: bool = True, **kwargs) -> None:
    """Print a summary of the functions in the graph."""
    print(functions_str(graph=graph, examples=examples, **kwargs), file=file)


def namespaces_table_df(graph: BELGraph, examples: bool = True) -> pd.DataFrame:
    """Create a dataframe describing the namespaces in the graph."""
    namespace_mapping = multidict((node.namespace, node) for node in graph if isinstance(node, BaseConcept))
    namespace_c = count_namespaces(graph)
    if not examples:
        return pd.DataFrame(namespace_c.most_common(), columns=['Namespace', 'Count'])
    return pd.DataFrame(
        [
            (
                prefix,
                bioregistry.get_name(prefix),
                count,
                random.choice(namespace_mapping[prefix]) if prefix in namespace_mapping else '',  # noqa:S311
            )
            for prefix, count in namespace_c.most_common()
        ],
        columns=['Prefix', 'Name', 'Count', 'Example'],
    )


def namespaces_str(graph: BELGraph, examples: bool = True, add_count: bool = True, **kwargs) -> None:
    """Make a summary string of the namespaces in the graph."""
    df = namespaces_table_df(graph, examples=examples)
    headers = list(df.columns)
    if add_count:
        headers[0] += ' ({})'.format(len(df.index))
    return tabulate(df.values, headers=headers, **kwargs)


def namespaces(graph: BELGraph, file: Optional[TextIO] = None, examples: bool = True, **kwargs) -> None:
    """Print a summary of the namespaces in the graph."""
    print(namespaces_str(graph=graph, examples=examples, **kwargs), file=file)


def edge_table_df(graph: BELGraph, *, examples: bool = True, minimum: Optional[int] = None) -> pd.DataFrame:
    """Create a dataframe describing the edges in the graph."""
    edge_mapping = multidict(
        (f'{u.function} {d[RELATION]} {v.function}', graph.edge_to_bel(u, v, d, use_identifiers=True))
        for u, v, d in graph.edges(data=True)
        if d[RELATION] not in TWO_WAY_RELATIONS or u.function > v.function
    )
    edge_c = Counter({top_level_edge: len(edges) for top_level_edge, edges in edge_mapping.items()})
    if examples:
        rows = [
            (top_level_edge, count, random.choice(edge_mapping[top_level_edge]))  # noqa:S311
            for top_level_edge, count in edge_c.most_common()
            if not minimum or count >= minimum
        ]
        columns = ['Edge Type', 'Count', 'Example']
    else:
        rows = edge_c.most_common()
        if minimum:
            rows = [(k, count) for k, count in rows if count >= minimum]
        columns = ['Edge Type', 'Count']
    return pd.DataFrame(rows, columns=columns)


def edges_str(
    graph: BELGraph,
    *,
    examples: bool = True,
    add_count: bool = True,
    minimum: Optional[int] = None,
    **kwargs,
) -> str:
    """Make a summary str of the edges in the graph."""
    df = edge_table_df(graph, examples=examples, minimum=minimum)
    headers = list(df.columns)
    if add_count:
        headers[0] += ' ({})'.format(intword(len(df.index)))
    return tabulate(df.values, headers=headers, **kwargs)


def edges(
    graph: BELGraph,
    *,
    examples: bool = True,
    minimum: Optional[int] = None,
    file: Optional[TextIO] = None,
    **kwargs,
) -> None:
    """Print a summary of the edges in the graph."""
    print(edges_str(graph=graph, examples=examples, minimum=minimum, **kwargs), file=file)


def citations(graph: BELGraph, n: Optional[int] = 15, file: Optional[TextIO] = None) -> None:
    """Print a summary of the citations in the graph."""
    edge_mapping = multidict(
        ((data[CITATION][NAMESPACE], data[CITATION][IDENTIFIER]), graph.edge_to_bel(u, v, data))
        for u, v, data in graph.edges(data=True)
        if CITATION in data
    )
    edge_c = Counter({top_level_edge: len(edges) for top_level_edge, edges in edge_mapping.items()})
    df = pd.DataFrame(
        [
            (':'.join(top_level_edge), count, random.choice(edge_mapping[top_level_edge]))  # noqa:S311
            for top_level_edge, count in edge_c.most_common(n=n)
        ],
        columns=['Citation', 'Count', 'Example'],
    )

    if n is None or len(edge_mapping) < n:
        print('{} Citation Count: {}'.format(graph, len(edge_mapping)))
    else:
        print('{} Citation Count: {} (Showing top {})'.format(graph, len(edge_mapping), n))
    print(tabulate(df.values, headers=df.columns), file=file)
