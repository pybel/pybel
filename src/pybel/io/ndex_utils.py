# -*- coding: utf-8 -*-

"""

NDEx
~~~~
This package provides a wrapper around :func:`pybel.to_cx` and NDEx
`client <https://github.com/ndexbio/ndex-python>`_ to allow for easy upload and download of BEL documents to the
`NDEx <http://www.ndexbio.org/>`_ database.

The programmatic API also provides options for specifying username and password. By default, it checks the environment 
variables: ``NDEX_USERNAME`` and ``NDEX_PASSWORD``.

"""

import logging
import os

from ndex.client import Ndex
from requests.compat import urlsplit

from .cx import from_cx, to_cx

__all__ = [
    'to_ndex',
    'from_ndex',
]

log = logging.getLogger(__name__)

#: The name of the environment variable to search or the NDEx username
NDEX_USERNAME = 'NDEX_USERNAME'

#: The name of the environment variable to search or the NDEx password
NDEX_PASSWORD = 'NDEX_PASSWORD'


def build_ndex_client(username=None, password=None, debug=False):
    """Builds a NDEx client by checking environmental variables.

    It has been requested that the :code:`ndex-client` has this functionality built-in by this GitHub 
    `issue <https://github.com/ndexbio/ndex-python/issues/9>`_

    :param str username: NDEx username
    :param str password: NDEx password
    :param bool debug: If true, turn on NDEx client debugging
    :return: An NDEx client
    :rtype: ndex.client.Ndex
    """
    if username is None and NDEX_USERNAME in os.environ:
        username = os.environ[NDEX_USERNAME]
        log.info('got NDEx username from environment: %s', username)

    if password is None and NDEX_PASSWORD in os.environ:
        password = os.environ[NDEX_PASSWORD]
        log.info('got NDEx password from environment')

    return Ndex(username=username, password=password, debug=debug)


def cx_to_ndex(cx, username=None, password=None, debug=False):
    """Uploads a CX document to NDEx. Not necessarily specific to PyBEL.

    :param list cx: A CX JSON dictionary
    :param str username: NDEx username
    :param str password: NDEx password
    :param bool debug: If true, turn on NDEx client debugging
    :return: The UUID assigned to the network by NDEx
    :rtype: str
    """
    ndex = build_ndex_client(username=username, password=password, debug=debug)
    res = ndex.save_new_network(cx)

    url_parts = urlsplit(res).path
    network_id = url_parts.split('/')[-1]

    return network_id


def to_ndex(graph, username=None, password=None, debug=False):
    """Uploads a BEL graph to NDEx

    :param BELGraph graph: A BEL graph
    :param str username: NDEx username
    :param str password: NDEx password
    :param bool debug: If true, turn on NDEx client debugging
    :return: The UUID assigned to the network by NDEx
    :rtype: str

    Example Usage:

    >>> import pybel
    >>> graph = pybel.from_url('http://resources.openbel.org/belframework/20150611/knowledge/small_corpus.bel')
    >>> pybel.to_ndex(graph)
    """
    cx = to_cx(graph)
    return cx_to_ndex(cx, username=username, password=password, debug=debug)


def from_ndex(network_id, username=None, password=None, debug=False):
    """Downloads a BEL Graph from NDEx

    .. warning:: This function only will work for CX documents that have been originally exported from PyBEL

    :param str network_id: The UUID assigned to the network by NDEx
    :param str username: NDEx username
    :param str password: NDEx password
    :param bool debug: If true, turn on NDEx client debugging
    :return: A BEL graph
    :rtype: BELGraph

    Example Usage:

    >>> from pybel import from_ndex
    >>> network_id = '1709e6f3-04a1-11e7-aba2-0ac135e8bacf'
    >>> graph = from_ndex(network_id)
    """
    ndex = build_ndex_client(username, password, debug)
    res = ndex.get_network_as_cx_stream(network_id)
    cx = res.json()
    graph = from_cx(cx)
    return graph
