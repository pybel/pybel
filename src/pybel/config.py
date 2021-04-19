# -*- coding: utf-8 -*-

"""Connection configuration for PyBEL."""

import logging

import pystow

__all__ = [
    'connection',
    'PYBEL_MINIMUM_IMPORT_VERSION',
    'PYBEL_HOME',
]

logger = logging.getLogger(__name__)

#: The last PyBEL version where the graph data definition changed
PYBEL_MINIMUM_IMPORT_VERSION = 0, 14, 0

PYBEL_HOME = pystow.join('pybel')
DEFAULT_CACHE_NAME = 'pybel_{}.{}.{}_cache.db'.format(*PYBEL_MINIMUM_IMPORT_VERSION)
DEFAULT_CACHE_PATH = pystow.join('pybel', name=DEFAULT_CACHE_NAME)
#: The default cache connection string uses sqlite.
DEFAULT_CACHE_CONNECTION = 'sqlite:///' + DEFAULT_CACHE_PATH.as_posix()

connection = pystow.get_config(
    'pybel',
    'connection',
    default=DEFAULT_CACHE_CONNECTION,
)
