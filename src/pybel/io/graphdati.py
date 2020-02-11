# -*- coding: utf-8 -*-

"""Conversion functions for BEL graphs with GraphDati."""

import gzip
import json
from typing import Any, List, Mapping, TextIO, Union

from networkx.utils import open_file

from pybel import BELGraph
from pybel.canonicalize import edge_to_tuple
from pybel.constants import CITATION, CITATION_DB, CITATION_IDENTIFIER, EVIDENCE

__all__ = [
    'to_graphdati',
    'to_graphdati_file',
    'to_graphdati_gz',
    'to_graphdati_jsons',
]

NanopubMapping = Mapping[str, Mapping[str, Any]]

SCHEMA_URI = 'https://github.com/belbio/schemas/blob/master/schemas/nanopub_bel-1.0.0.yaml'


@open_file(1, mode='w')
def to_graphdati_file(graph: BELGraph, path: Union[str, TextIO], **kwargs) -> None:
    """Write this graph as GraphDati JSON to a file.

    :param graph: A BEL graph
    :param path: A path or file-like
    """
    json.dump(to_graphdati(graph), path, ensure_ascii=False, **kwargs)


def to_graphdati_gz(graph, path: str, **kwargs) -> None:
    """Write a graph as GraphDati JSON to a gzip file."""
    with gzip.open(path, 'wt') as file:
        json.dump(to_graphdati(graph), file, ensure_ascii=False, **kwargs)


def to_graphdati_jsons(graph: BELGraph, **kwargs) -> str:
    """Dump this graph as a GraphDati JSON object to a string."""
    return json.dumps(to_graphdati(graph), ensure_ascii=False, **kwargs)


def to_graphdati(graph: BELGraph) -> List[NanopubMapping]:
    """Export a GraphDati list using the nanopub """
    return [
        _make_nanopub(graph, u, v, k, d)
        for u, v, k, d in graph.edges(keys=True, data=True)
    ]


def _make_nanopub(graph, u, v, k, d) -> NanopubMapping:
    return dict(
        nanopub=dict(
            schema_url=SCHEMA_URI,
            type=dict(name='BEL', version='2.1.0'),
            annotations=_get_annotations(d),
            citation=_get_citation(d),
            assertions=_get_assertions(u, v, d),
            evidence=_get_evidence(d),
            metadata=_get_metadata(graph, d),
            id='pybel_{}'.format(k),
        ),
    )


def _get_assertions(u, v, d):
    return [
        dict(zip(
            ('subject', 'relation', 'object'),
            edge_to_tuple(u, v, d, use_identifiers=True),
        )),
    ]


def _get_evidence(d):
    return d.get(EVIDENCE, 'Not Available')


def _get_citation(d):
    citation = d.get(CITATION)
    if citation is None:
        reference = 'Not Available'
    else:
        reference = '{}:{}'.format(citation[CITATION_DB], citation[CITATION_IDENTIFIER])
    return dict(reference=reference)


def _get_metadata(graph: BELGraph, d):
    return dict(
        author=graph.authors,
        version=graph.version,
    )  # TODO later


def _get_annotations(d):
    return []  # TODO later


def _main():
    import pybel.examples
    import os

    for x in dir(pybel.examples):
        y = getattr(pybel.examples, x)
        if isinstance(y, BELGraph):
            name = y.name.lower().replace(' ', '_')
            to_graphdati_file(
                y,
                os.path.join(os.path.expanduser('~'), 'Desktop', '{}.graphdati.json'.format(name)),
                indent=2,
            )


if __name__ == '__main__':
    _main()
