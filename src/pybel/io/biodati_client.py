# -*- coding: utf-8 -*-

"""Transport functions for `BioDati <https://biodati.com/>`_.

BioDati is a paid, closed-source platform for hosting BEL content. However,
they do have a demo instance running at https://studio.demo.biodati.com with which the examples
in this module will be described.

As noted in the transport functions for BioDati, you should change the URLs to point to your own
instance of BioDati. If you're looking for an open source storage system for  hosting your own BEL content,
you may consider `BEL Commons <https://github.com/bel-commons/bel-commons>`_, with the caveat that it is
currently maintained in an academic capacity. Disclosure: BEL Commons is developed by the developers of PyBEL.
"""

import json
import logging
from io import BytesIO
from typing import Optional

import requests
from more_itertools import chunked
from tqdm import tqdm

from .graphdati import _iter_graphdati, from_graphdati, to_graphdati
from ..struct import BELGraph

__all__ = [
    'to_biodati',
    'from_biodati',
]

logger = logging.getLogger(__name__)


def to_biodati(  # noqa: S107
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
    :param base_url: The BioDati nanopub store base url. Defaults to "https://nanopubstore.demo.biodati.com" for
     the demo server's nanopub store
    :param chunksize: The number of nanopubs to post at a time. By default, does all.

    .. warning::

        BioDati does not support large uploads (yet?).

    .. warning::

        The default public BioDati server has been put here. You should
        switch it to yours. It will look like ``https://nanopubstore.<YOUR NAME>.biodati.com``.
    """
    biodati_client = BiodatiClient(username, password, base_url)
    if chunksize:
        return biodati_client.post_graph_chunked(graph, chunksize, **kwargs)
    else:
        return biodati_client.post_graph(graph, **kwargs)


def from_biodati(  # noqa: S107
    network_id: str,
    username: str = 'demo@biodati.com',
    password: str = 'demo',
    base_url: str = 'https://networkstore.demo.biodati.com',
) -> BELGraph:
    """Get a graph from a BioDati network store based on its network identifier.

    :param network_id: The internal identifier of the network you want to download.
    :param username: The email address to log in to BioDati. Defaults to "demo@biodati.com" for the demo server
    :param password: The password to log in to BioDati. Defaults to "demo" for the demo server
    :param base_url: The BioDati network store base url. Defaults to "https://networkstore.demo.biodati.com" for
     the demo server's network store

    Example usage:

    .. code-block:: python

        from pybel import get_biodati_network
        network_id = '01E46GDFQAGK5W8EFS9S9WMH12'  # COVID-19 graph example from Wendy Zimmermann
        graph = from_biodati(
            network_id=network_id,
            username='demo@biodati.com',
            password='demo',
            base_url='https://networkstore.demo.biodati.com',
        )
        graph.summarize()

    .. warning::

        The default public BioDati server has been put here. You should
        switch it to yours. It will look like ``https://networkstore.<YOUR NAME>.biodati.com``.
    """
    biodati_client = BiodatiClient(username, password, base_url)
    return biodati_client.get_graph(network_id)


class BiodatiClient:
    """A client for the BioDati nanopub store and network store's APIs."""

    def __init__(self, username: str, password: str, base_url):
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
        return self._help_request(requests.post, endpoint, **kwargs)

    def get(self, endpoint: str, **kwargs):
        """Send a get request to BioDati."""
        return self._help_request(requests.get, endpoint, **kwargs)

    def _help_request(self, requester, endpoint: str, **kwargs):
        """Send a request to BioDati."""
        url = '{}/{}'.format(self.base_url, endpoint)
        logger.info('requesting %s with params %s', url, kwargs.get('params', {}))
        headers = {'Authorization': '{} {}'.format(self.token_type, self.id_token)}
        return requester(url, headers=headers, **kwargs)

    def get_graph(self, network_id: str) -> BELGraph:
        """Get a graph from BioDati."""
        return from_graphdati(self.get_graph_json(network_id))

    def get_graph_json(self, network_id: str, network_format: str = 'normal'):
        """Get the graph JSON."""
        res = self.get(
            'networks/{network_id}'.format(network_id=network_id),
            params={'format': network_format},
        )
        # FIXME network_format='full' causes internal server error currently
        res_json = res.json()
        return res_json

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
    netowork_id = '01E46GDFQAGK5W8EFS9S9WMH12'
    graph = from_biodati(network_id=netowork_id)
    graph.summarize()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    _main()
