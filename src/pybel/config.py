# -*- coding: utf-8 -*-

"""Connection configuration for PyBEL."""

import json
import logging
import os

from .version import VERSION

__all__ = [
    'config',
    'connection',
    'PYBEL_MINIMUM_IMPORT_VERSION',
]

log = logging.getLogger(__name__)

#: The last PyBEL version where the graph data definition changed
PYBEL_MINIMUM_IMPORT_VERSION = 0, 13, 0

config = {}

PYBEL_CACHE_DIRECTORY = 'PYBEL_CACHE_DIRECTORY'
DEFAULT_CACHE_DIRECTORY = os.path.join(os.path.expanduser('~'), '.pybel')
#: The default directory where PyBEL files, including logs and the  default cache, are stored. Created if not exists.
CACHE_DIRECTORY = os.environ.get(PYBEL_CACHE_DIRECTORY, DEFAULT_CACHE_DIRECTORY)

DEFAULT_CACHE_NAME = 'pybel_{}.{}.{}_cache.db'.format(*PYBEL_MINIMUM_IMPORT_VERSION)
DEFAULT_CACHE_PATH = os.path.join(CACHE_DIRECTORY, DEFAULT_CACHE_NAME)
#: The default cache connection string uses sqlite.
DEFAULT_CACHE_CONNECTION = 'sqlite:///' + DEFAULT_CACHE_PATH

PYBEL_CONFIG_DIRECTORY = 'PYBEL_CONFIG_DIRECTORY'
PYBEL_DEV_CONFIG_DIRECTORY = 'PYBEL_DEV_CONFIG_DIRECTORY'
DEFAULT_CONFIG_DIRECTORY = os.path.join(os.path.expanduser('~'), '.config')
if VERSION.endswith('-dev'):
    CONFIG_DIRECTORY = os.environ.get(PYBEL_DEV_CONFIG_DIRECTORY, os.path.join(DEFAULT_CONFIG_DIRECTORY, 'pybel-dev'))
else:
    CONFIG_DIRECTORY = os.environ.get(PYBEL_CONFIG_DIRECTORY, os.path.join(DEFAULT_CONFIG_DIRECTORY, 'pybel'))

PYBEL_CONFIG_PATH = 'PYBEL_CONFIG_PATH'
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIRECTORY, 'config.json')
CONFIG_PATH = os.environ.get(PYBEL_CONFIG_PATH, DEFAULT_CONFIG_PATH)

if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH) as file:
        config.update(json.load(file))

#: The environment variable that contains the default SQL connection information for the PyBEL cache
PYBEL_CONNECTION = 'PYBEL_CONNECTION'

if PYBEL_CONNECTION in os.environ:
    connection = os.environ[PYBEL_CONNECTION]
    log.info('got environment-defined connection: %s', connection)
elif PYBEL_CONNECTION in config:
    connection = config[PYBEL_CONNECTION]
    log.info('getting configured connection: %s', connection)
else:  # This means that there will have to be a cache directory created
    os.makedirs(CACHE_DIRECTORY, exist_ok=True)
    connection = DEFAULT_CACHE_CONNECTION
    log.info('no configuration found, using default sqlite connection %s', connection)
