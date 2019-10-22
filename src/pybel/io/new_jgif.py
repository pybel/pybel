# -*- coding: utf-8 -*-

"""Export JGIF for TriplesDB."""

import json
from typing import Any, Mapping, Optional, TextIO, Union

import requests
from networkx.utils import open_file

from pybel import BELGraph
from pybel.canonicalize import edge_to_tuple
from pybel.constants import ANNOTATIONS

__all__ = [
    'post_jgif',
    'to_jgif_file',
    'to_jgif',
]

DEFAULT_API = ''


def post_jgif(graph: BELGraph, url: Optional[str] = None) -> requests.Response:
    """Post the JGIF to a given URL."""
    jgif = to_jgif(graph)
    return requests.post(url, data=jgif)


@open_file(1, mode='w')
def to_jgif_file(graph: BELGraph, file: Union[str, TextIO], **kwargs) -> None:
    """Write JGIF to a file."""
    jgif = to_jgif(graph)
    json.dump(jgif, file, **kwargs)


def to_jgif(graph: BELGraph) -> Mapping[str, Any]:
    """Generate JGIF from the graph."""
    rv = dict(
        label=graph.name,
        metadata=dict(
            version=graph.version,
            description=graph.description,
            author=graph.authors,
        ),
        edges=[],
    )

    nodes = {}

    for u, v, k, d in graph.edges(keys=True, data=True):
        source, r, target = edge_to_tuple(u, v, d)

        for x, y in ((u, source), (v, target)):
            if y not in nodes:
                nodes[y] = dict(label=source, id=source, type=x.function)

        rv['edges'].append(dict(
            label=' '.join((source, r, target)),
            source=source,
            target=target,
            relation=r,
            annotations=[
                dict(type=key, label=value, id=value)
                for key, values in d.get(ANNOTATIONS, {}).items()
                for value in values
            ]
        ))

    rv['nodes'] = list(nodes.values())

    return rv
