# -*- coding: utf-8 -*-

"""This module facilitates rudimentary data exchange with `PyBEL Web <https://pybel.scai.fraunhofer.de>`_."""

import requests

from .nodelink import to_json

__all__ = [
    'to_web',
    'from_web',
]

DEFAULT_SERVICE_URL = 'https://pybel.scai.fraunhofer.de'
RECIEVE_ENDPOINT = '/api/receive'


def to_web(graph, host=None):
    """Sends a graph to the receiver service and returns the :mod:`requests` response object

    :param pybel.BELGraph graph: A BEL network
    :param str host: The location of the PyBEL web server. Defaults to :data:`DEFAULT_SERVICE_URL`
    :return: The response object from :mod:`requests`
    :rtype: requests.Response
    """
    host = DEFAULT_SERVICE_URL if host is None else host
    url = host + RECIEVE_ENDPOINT
    return requests.post(url, json=to_json(graph), headers={'content-type': 'application/json'})


def from_web(network_id, service=None):
    """Retrieves a public network from PyBEL Web. In the future, this function may be extended to support
    authentication.

    :param int network_id: The PyBEL web network identifier
    :param service: The location of the PyBEL web server. Defaults to :data:`DEFAULT_SERVICE_URL`
    :rtype: pybel.BELGraph

    .. warning:: This is not implemented yet.
    """
    raise NotImplementedError
