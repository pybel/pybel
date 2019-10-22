# -*- coding: utf-8 -*-

"""Export JGIF for TriplesDB."""

import json
from typing import Mapping, Optional, TextIO, Union

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


def post_jgif(graph: BELGraph, base_url: Optional[str] = None) -> requests.Response:
    url = _build_endpoint(base_url)
    jgif = to_jgif(graph)
    return requests.post(url, data=jgif)


def _build_endpoint(url):  # FIXME
    return url


@open_file(1, mode='w')
def to_jgif_file(graph: BELGraph, file: Union[str, TextIO], **kwargs) -> None:
    jgif = to_jgif(graph)
    json.dump(jgif, file, **kwargs)


def to_jgif(graph: BELGraph) -> Mapping:
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


if __name__ == '__main__':
    from pybel.examples import sialic_acid_graph

    to_jgif_file(sialic_acid_graph, '/Users/cthoyt/Desktop/sialic_acid.bel.jgif.json')
