# -*- coding: utf-8 -*-

"""This module facilitates rudimentary data exchange with `PyBEL Web <https://pybel.scai.fraunhofer.de>`_.

.. warning::

    These functions are hard to unit test because they rely on a web service that isn't *exactly* stable yet. Stay
    tuned!
"""

import requests

from .nodelink import from_json, to_json
from ..constants import DEFAULT_SERVICE_URL

__all__ = [
    'to_web',
    'from_web',
]

RECIEVE_ENDPOINT = '/api/receive'
GET_ENDPOINT = '/api/network/{}/export/nodelink'


def to_web(graph, host=None):
    """Sends a graph to the receiver service and returns the :mod:`requests` response object

    :param pybel.BELGraph graph: A BEL network
    :param Optional[str] host: The location of the PyBEL web server. Defaults to :data:`pybel.constants.DEFAULT_SERVICE_URL`
    :return: The response object from :mod:`requests`
    :rtype: requests.Response
    """
    host = host or DEFAULT_SERVICE_URL
    url = host + RECIEVE_ENDPOINT
    return requests.post(url, json=to_json(graph), headers={'content-type': 'application/json'})


def from_web(network_id, host=None):
    """Retrieves a public network from PyBEL Web. In the future, this function may be extended to support
    authentication.

    :param int network_id: The PyBEL Web network identifier
    :param Optional[str] host: The location of the PyBEL web server. Defaults to :data:`pybel.constants.DEFAULT_SERVICE_URL`
    :rtype: pybel.BELGraph
    """
    host = host or DEFAULT_SERVICE_URL
    url = host + GET_ENDPOINT.format(network_id)
    res = requests.get(url)
    graph_json = res.json()
    graph = from_json(graph_json)
    return graph
