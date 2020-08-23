# -*- coding: utf-8 -*-

"""Streamable BEL as JSON."""

import gzip
import json
from typing import Any, Iterable, List, TextIO, Union

from networkx.utils import open_file

from .nodelink import _augment_node, _prepare_graph_dict, _recover_graph_dict
from ..constants import CITATION, SOURCE_MODIFIER, TARGET_MODIFIER
from ..language import CitationDict
from ..struct.graph import BELGraph, _handle_modifier
from ..tokens import parse_result_to_dsl
from ..utils import hash_edge

__all__ = [
    'to_sbel_file',
    'to_sbel',
    'to_sbel_gz',
    'from_sbel',
    'from_sbel_gz',
    'from_sbel_file',
]

SBEL = Any


@open_file(1, mode='w')
def to_sbel_file(graph: BELGraph, path: Union[str, TextIO], separators=(',', ':'), **kwargs) -> None:
    """Write this graph as BEL JSONL to a file.

    :param graph: A BEL graph
    :param separators: The separators used in :func:`json.dumps`
    :param path: A path or file-like
    """
    for i in iterate_sbel(graph):
        print(json.dumps(i, ensure_ascii=False, separators=separators, **kwargs), file=path)


def to_sbel_gz(graph: BELGraph, path: str, separators=(',', ':'), **kwargs) -> None:
    """Write a graph as BEL JSONL to a gzip file.

    :param graph: A BEL graph
    :param separators: The separators used in :func:`json.dumps`
    :param path: A path for a gzip file
    """
    with gzip.open(path, 'wt') as file:
        to_sbel_file(graph, file, separators=separators, **kwargs)


def to_sbel(graph: BELGraph) -> List[SBEL]:
    """Create a list of JSON dictionaries corresponding to lines in BEL JSONL."""
    return list(iterate_sbel(graph))


def iterate_sbel(graph: BELGraph) -> Iterable[SBEL]:
    """Iterate over JSON dictionaries corresponding to lines in BEL JSONL."""
    g = graph.graph.copy()
    _prepare_graph_dict(g)
    yield g
    for u, v, k, d in graph.edges(data=True, keys=True):
        yield {
            'source': _augment_node(u),
            'target': _augment_node(v),
            'key': k,
            **d,
        }


def from_sbel(it: Iterable[SBEL], includes_metadata: bool = True) -> BELGraph:
    """Load a BEL graph from an iterable of dictionaries corresponding to lines in BEL JSONL.

    :param it: An iterable of dictionaries.
    :param includes_metadata: By default, interprets the first element of the iterable as the graph's metadata.
     Switch to ``False`` to disable.
    :return: A BEL graph
    """
    it = iter(it)
    rv = BELGraph()
    if includes_metadata:
        rv.graph.update(next(it))
        _recover_graph_dict(rv)
    add_sbel(rv, it)
    return rv


def add_sbel(graph: BELGraph, it: Iterable[SBEL]) -> None:
    """Add dictionaries to a BEL graph.

    :param graph: A BEL graph
    :param it: An iterable of dictionaries.
    """
    for data in it:
        add_sbel_row(graph, data)


def add_sbel_row(graph: BELGraph, data: SBEL) -> str:
    """Add a single SBEL data dictionary to a graph."""
    u = parse_result_to_dsl(data['source'])
    v = parse_result_to_dsl(data['target'])
    edge_data = {
        k: v
        for k, v in data.items()
        if k not in {'source', 'target', 'key'}
    }
    for side in (SOURCE_MODIFIER, TARGET_MODIFIER):
        side_data = edge_data.get(side)
        if side_data:
            _handle_modifier(side_data)
    if CITATION in edge_data:
        edge_data[CITATION] = CitationDict(**edge_data[CITATION])
    return graph.add_edge(u, v, key=hash_edge(u, v, edge_data), **edge_data)


@open_file(0, mode='r')
def from_sbel_file(path: Union[str, TextIO]) -> BELGraph:
    """Build a graph from the BEL JSONL contained in the given file.

    :param path: A path or file-like
    """
    return from_sbel((
        json.loads(line)
        for line in path
    ))


def from_sbel_gz(path: str) -> BELGraph:
    """Read a graph as BEL JSONL from a gzip file."""
    with gzip.open(path, 'rt') as file:
        return from_sbel_file(file)
