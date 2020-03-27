# -*- coding: utf-8 -*-

"""Conversion functions for BEL graphs with GraphDati."""

import gzip
import json
from io import BytesIO
from typing import Any, Iterable, List, Mapping, Optional, TextIO, Union

import requests
from more_itertools import chunked
from networkx.utils import open_file
from tqdm import tqdm

from ..canonicalize import edge_to_tuple
from ..constants import CITATION, CITATION_DB, CITATION_IDENTIFIER, EVIDENCE
from ..struct import BELGraph

__all__ = [
    'to_graphdati',
    'to_graphdati_file',
    'to_graphdati_gz',
    'to_graphdati_jsons',
    'to_graphdati_jsonl',
    'to_graphdati_jsonl_gz',
    'BioDatiClient',
    'post_graphdati',
]

NanopubMapping = Mapping[str, Mapping[str, Any]]

SCHEMA_URI = 'https://github.com/belbio/schemas/blob/master/schemas/nanopub_bel-1.0.0.yaml'


@open_file(1, mode='w')
def to_graphdati_file(graph: BELGraph, path: Union[str, TextIO], use_identifiers: bool = True, **kwargs) -> None:
    """Write this graph as GraphDati JSON to a file.

    :param graph: A BEL graph
    :param path: A path or file-like
    """
    json.dump(to_graphdati(graph, use_identifiers=use_identifiers), path, ensure_ascii=False, **kwargs)


def to_graphdati_gz(graph: BELGraph, path: str, **kwargs) -> None:
    """Write a graph as GraphDati JSON to a gzip file."""
    with gzip.open(path, 'wt') as file:
        to_graphdati_file(graph, file, **kwargs)


def to_graphdati_jsons(graph: BELGraph, **kwargs) -> str:
    """Dump this graph as a GraphDati JSON object to a string.

    :param graph: A BEL graph
    """
    return json.dumps(to_graphdati(graph), ensure_ascii=False, **kwargs)


@open_file(1, mode='w')
def to_graphdati_jsonl(graph, file, use_identifiers: bool = True, use_tqdm: bool = True):
    """Write this graph as a GraphDati JSON lines file."""
    nanopubs = _iter_graphdati(graph, use_identifiers=use_identifiers)
    if use_tqdm:
        nanopubs = tqdm(nanopubs, desc='Outputting GraphDati JSONL', total=graph.number_of_edges())
    for nanopub in nanopubs:
        print(json.dumps(nanopub), file=file)


def to_graphdati_jsonl_gz(graph: BELGraph, path: str, **kwargs) -> None:
    """Write a graph as GraphDati JSONL to a gzip file."""
    with gzip.open(path, 'wt') as file:
        to_graphdati_jsonl(graph, file, **kwargs)


def to_graphdati(graph, use_identifiers: bool = True) -> List[NanopubMapping]:
    """Export a GraphDati list using the nanopub.

    :param graph: A BEL graph
    :param use_identifiers: use OBO-style identifiers
    """
    return list(_iter_graphdati(graph, use_identifiers=use_identifiers))


def _iter_graphdati(graph, use_identifiers: bool = True) -> Iterable[NanopubMapping]:
    for u, v, k, d in graph.edges(keys=True, data=True):
        yield _make_nanopub(graph, u, v, k, d, use_identifiers)


def _make_nanopub(graph: BELGraph, u, v, k, d, use_identifiers) -> NanopubMapping:
    return dict(
        nanopub=dict(
            schema_uri=SCHEMA_URI,
            type=dict(name='BEL', version='2.1.0'),
            annotations=_get_annotations(d),
            citation=_get_citation(d),
            assertions=_get_assertions(u, v, d, use_identifiers),
            evidence=_get_evidence(d),
            metadata=_get_metadata(graph, d),
            id='pybel_{}'.format(k),
        ),
    )


def _get_assertions(u, v, d, use_identifiers):
    return [
        dict(zip(
            ('subject', 'relation', 'object'),
            edge_to_tuple(u, v, d, use_identifiers=use_identifiers),
        )),
    ]


def _get_evidence(d):
    return d.get(EVIDENCE, 'Not Available')


def _get_citation(d):
    citation = d.get(CITATION)
    rv = {}
    if citation is None:
        rv['reference'] = 'Not Available'
    else:
        rv['database'] = dict(name=citation[CITATION_DB], id=citation[CITATION_IDENTIFIER])
    return rv


def _get_metadata(graph: BELGraph, _):
    return dict(
        gd_creator=graph.authors,
        version=graph.version,
    )  # TODO later


def _get_annotations(d):
    return []  # TODO later


def post_graphdati(  # noqa: S107
    graph: BELGraph,
    username: str = 'demo@biodati.com',
    password: str = 'demo',
    base_url: str = 'https://nanopubstore.demo.biodati.com',
    chunksize: Optional[int] = None,
    **kwargs
) -> requests.Response:
    """Post this graph to a BioDati server.

    :param graph: A BEL graph
    :param username: The email address to log in to BioDati. Defaults to "demo@biodati.com" for the demo server
    :param password: The password to log in to BioDati. Defaults to "demo" for the demo server
    :param base_url: The BioDati server base url. Defaults to "https://nanopubstore.demo.biodati.com" for the demo
     server
    :param chunksize: The number of nanopubs to post at a time. By default, does all.

    .. warning::

        The default public BioDati server has been put here. You should
        switch it to yours.
    """
    connection = BioDatiClient(username, password, base_url)
    if chunksize:
        return connection.post_graph_chunked(graph, chunksize, **kwargs)
    else:
        return connection.post_graph(graph, **kwargs)


class BioDatiClient:
    """A connection to the BioDati API."""

    def __init__(self, username, password, base_url):
        self.base_url = base_url.rstrip('/')
        self.username = username
        res = requests.post(
            '{}/token'.format(base_url),
            data=dict(username=username, password=password),
        )
        token_dict = res.json()
        self.token_type = token_dict['token_type']
        self.id_token = token_dict['id_token']
        self.access_token = token_dict['access_token']

    def post(self, endpoint: str, **kwargs):
        """Send a post request to BioDati."""
        url = '{}/{}'.format(self.base_url, endpoint)
        headers = {'Authorization': '{} {}'.format(self.token_type, self.id_token)}
        return requests.post(url, headers=headers, **kwargs)

    def post_graph(self, graph: BELGraph, **kwargs) -> requests.Response:
        """Post the graph to BioDati."""
        return self.post_graph_json(to_graphdati(graph), **kwargs)

    def post_graph_chunked(self, graph: BELGraph, chunksize: int, use_tqdm: bool = True, **kwargs):
        """Post the graph to BioDati in chunks, when the graph is too big for a normal upload."""
        iterable = _iter_graphdati(graph)
        if use_tqdm:
            iterable = tqdm(iterable, total=graph.number_of_edges())
        res = None
        for chunk in chunked(iterable, chunksize):
            res = self.post_graph_json(chunk, **kwargs)
        return res

    def post_graph_json(self, graph_json, **kwargs) -> requests.Response:
        """Post the GraphDati object to BioDati."""
        file = BytesIO()
        file.write(json.dumps(graph_json).encode('utf-8'))
        file.seek(0)
        return self.post_graph_file(file, **kwargs)

    def post_graph_file(
        self,
        file,
        overwrite: bool = False,
        validate: bool = True,
        email: bool = False,
    ) -> requests.Response:
        """Post a graph to BioDati."""
        params = dict(overwrite=overwrite, validate=validate)
        if isinstance(email, str):
            params['email'] = email
        elif email:
            params['email'] = self.username

        return self.post(
            'nanopubs/import/file',
            files=dict(file=file),
            params=params,
        )


def _main():
    """Run with python -m pybel.io.graphdati."""
    import pybel.examples
    import os

    for x in dir(pybel.examples):
        graph = getattr(pybel.examples, x)
        if isinstance(graph, BELGraph):
            name = graph.name.lower().replace(' ', '_')
            to_graphdati_file(
                graph,
                os.path.join(os.path.expanduser('~'), 'Desktop', '{}.graphdati.json'.format(name)),
                indent=2,
            )
            post_graphdati(graph, chunksize=2)


if __name__ == '__main__':
    _main()
