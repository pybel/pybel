# -*- coding: utf-8 -*-

"""Connection configuration for PyBEL."""

import configparser
import logging
import os

from .version import VERSION

__all__ = [
    'config',
    'connection',
    'PYBEL_MINIMUM_IMPORT_VERSION',
    'CACHE_DIRECTORY',
]

logger = logging.getLogger(__name__)

#: The last PyBEL version where the graph data definition changed
PYBEL_MINIMUM_IMPORT_VERSION = 0, 14, 0

config = {}

PYBEL_CACHE_DIRECTORY = 'PYBEL_CACHE_DIRECTORY'
DEFAULT_CACHE_DIRECTORY = os.path.join(os.path.expanduser('~'), '.pybel')
#: The default directory where PyBEL files, including logs and the  default cache, are stored. Created if not exists.
CACHE_DIRECTORY = os.environ.get(PYBEL_CACHE_DIRECTORY, DEFAULT_CACHE_DIRECTORY)

DEFAULT_CACHE_NAME = 'pybel_{}.{}.{}_cache.db'.format(*PYBEL_MINIMUM_IMPORT_VERSION)
DEFAULT_CACHE_PATH = os.path.join(CACHE_DIRECTORY, DEFAULT_CACHE_NAME)
#: The default cache connection string uses sqlite.
DEFAULT_CACHE_CONNECTION = 'sqlite:///' + DEFAULT_CACHE_PATH


_CONFIG_DIRECTORY = os.path.join(os.path.expanduser('~'), '.pybel')
CONFIG_FILE_PATHS = [
    os.path.join(_CONFIG_DIRECTORY, 'pybel.ini'),
    os.path.join(_CONFIG_DIRECTORY, 'pybel.cfg'),
    os.path.join(_CONFIG_DIRECTORY, 'pybel', 'pybel.ini'),
    os.path.join(_CONFIG_DIRECTORY, 'pybel', 'pybel.cfg'),
    os.path.join(_CONFIG_DIRECTORY, 'pybel', 'config.ini'),
]
config_parser = configparser.ConfigParser()
config_parser.read(CONFIG_FILE_PATHS)
if 'pybel' in config_parser:
    config.update(config_parser['pybel'])
if VERSION.endswith('-dev') and 'pybel-dev' in config_parser:
    config.update(config_parser['pybel-dev'])

#: The environment variable that contains the default SQL connection information for the PyBEL cache
PYBEL_CONNECTION = 'PYBEL_CONNECTION'

if PYBEL_CONNECTION in os.environ:
    connection = os.environ[PYBEL_CONNECTION]
    logger.info('got environment-defined connection: %s', connection)
elif 'connection' in config:
    connection = config['connection']
    logger.info('getting configured connection: %s', connection)
else:  # This means that there will have to be a cache directory created
    os.makedirs(CACHE_DIRECTORY, exist_ok=True)
    connection = DEFAULT_CACHE_CONNECTION
    logger.info('no configuration found, using default sqlite connection %s', connection)
