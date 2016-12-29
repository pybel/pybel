"""Parsing, validation, and analysis of of BEL graphs"""

import os

from . import cli
from . import graph
from .constants import LARGE_CORPUS_URL, SMALL_CORPUS_URL, PYBEL_DIR
from .graph import *

__all__ = ['SMALL_CORPUS_URL', 'LARGE_CORPUS_URL'] + graph.__all__

__version__ = '0.3.0'

__title__ = 'PyBEL'
__description__ = 'Parsing, validation, and analysis of BEL graphs'
__url__ = 'https://github.com/pybel/pybel'

__author__ = 'Charles Tapley Hoyt, Andrej Konotopez, Christian Ebeling'
__email__ = 'charles.hoyt@scai.fraunhofer.de'

__license__ = 'Apache 2.0 License'
__copyright__ = 'Copyright (c) 2016 Charles Tapley Hoyt, Andrej Konotopez, Christian Ebeling'


def get_large_corpus(force_reload=False, **kwargs):
    """Gets the example large corpus"""
    path = os.path.join(PYBEL_DIR, 'large_corpus.gpickle')
    if os.path.exists(path) and not force_reload:
        return from_pickle(path)
    g = from_url(LARGE_CORPUS_URL, **kwargs)
    to_pickle(g, path)
    return g


def get_small_corpus(force_reload=False, **kwargs):
    """Gets the example small corpus"""
    path = os.path.join(PYBEL_DIR, 'small_corpus.gpickle')
    if os.path.exists(path) and not force_reload:
        return from_pickle(path)
    g = from_url(SMALL_CORPUS_URL, **kwargs)
    to_pickle(g, path)
    return g
