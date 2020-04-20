# -*- coding: utf-8 -*-

"""Transport functions for `BEL Commons <https://github.com/bel-commons/bel-commons>`_.

BEL Commons is a free, open-source platform for hosting BEL content. Because it was originally
developed and published in an academic capacity at Fraunhofer SCAI, a public instance can be
found at https://bel-commons-dev.scai.fraunhofer.de. However, this instance is only supported
out of posterity and will not be updated. If you would like to host your own instance of
BEL Commons, there are instructions on its GitHub page.
"""

import logging
import os
from typing import Optional

import requests

from .nodelink import from_nodelink, to_nodelink
from ..config import config
from ..constants import DEFAULT_SERVICE_URL, PYBEL_REMOTE_HOST, PYBEL_REMOTE_PASSWORD, PYBEL_REMOTE_USER
from ..struct.graph import BELGraph
from ..version import get_version

__all__ = [
    'to_bel_commons',
    'from_bel_commons',
]

logger = logging.getLogger(__name__)

RECIEVE_ENDPOINT = '/api/receive/'
GET_ENDPOINT = '/api/network/{}/export/nodelink'


def _get_config_or_env(name: str) -> Optional[str]:
    return config.get(name) or os.environ.get(name)


def _get_host() -> str:
    """Find the host.

    Has three possibilities:

    1. The PyBEL config entry ``PYBEL_REMOTE_HOST``, loaded in :mod:`pybel.constants`
    2. The environment variable ``PYBEL_REMOTE_HOST``
    3. The default service URL, :data:`pybel.constants.DEFAULT_SERVICE_URL`
    """
    return _get_config_or_env(PYBEL_REMOTE_HOST) or DEFAULT_SERVICE_URL


def _get_user() -> Optional[str]:
    return _get_config_or_env(PYBEL_REMOTE_USER)


def _get_password() -> Optional[str]:
    return _get_config_or_env(PYBEL_REMOTE_PASSWORD)


def to_bel_commons(
    graph: BELGraph,
    host: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    public: bool = False,
) -> requests.Response:
    """Send a graph to the receiver service and returns the :mod:`requests` response object.

    :param graph: A BEL graph
    :param host: The location of the BEL Commons server. Alternatively, looks up in PyBEL config with
     ``PYBEL_REMOTE_HOST`` or the environment as ``PYBEL_REMOTE_HOST`` Defaults to
     :data:`pybel.constants.DEFAULT_SERVICE_URL`
    :param user: Username for BEL Commons. Alternatively, looks up in PyBEL config with
     ``PYBEL_REMOTE_USER`` or the environment as ``PYBEL_REMOTE_USER``
    :param password: Password for BEL Commons. Alternatively, looks up in PyBEL config with
     ``PYBEL_REMOTE_PASSWORD`` or the environment as ``PYBEL_REMOTE_PASSWORD``
    :return: The response object from :mod:`requests`
    """
    if host is None:
        host = _get_host()
        logger.debug('using host: %s', host)

    if user is None:
        user = _get_user()

        if user is None:
            raise ValueError('no user found')

    if password is None:
        password = _get_password()

        if password is None:
            raise ValueError('no password found')

    url = host.rstrip('/') + RECIEVE_ENDPOINT

    response = requests.post(
        url,
        json=to_nodelink(graph),
        headers={
            'content-type': 'application/json',
            'User-Agent': 'PyBEL v{}'.format(get_version()),
            'bel-commons-public': 'true' if public else 'false',
        },
        auth=(user, password),
    )
    logger.debug('received response: %s', response)

    return response


def from_bel_commons(network_id: int, host: Optional[str] = None) -> BELGraph:
    """Retrieve a public network from BEL Commons.

    In the future, this function may be extended to support authentication.

    :param network_id: The BEL Commons network identifier
    :param host: The location of the BEL Commons server. Alternatively, looks up in PyBEL config with
     ``PYBEL_REMOTE_HOST`` or the environment as ``PYBEL_REMOTE_HOST`` Defaults to
     :data:`pybel.constants.DEFAULT_SERVICE_URL`
    """
    if host is None:
        host = _get_host()

    url = host + GET_ENDPOINT.format(network_id)
    res = requests.get(url)
    graph_json = res.json()
    graph = from_nodelink(graph_json)
    return graph
