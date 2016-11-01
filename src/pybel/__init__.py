"""Parsing, validation, and analysis of of BEL graphs"""

from __future__ import print_function

from . import cli
from . import graph
from .graph import *

small_corpus_url = 'http://resource.belframework.org/belframework/1.0/knowledge/small_corpus.bel'
large_corpus_url = 'http://resource.belframework.org/belframework/1.0/knowledge/large_corpus.bel'

__all__ = ['small_corpus_url', 'large_corpus_url'] + graph.__all__

__version__ = '0.2.4-dev'

__title__ = 'PyBEL'
__description__ = 'Parsing, validation, and analysis of BEL graphs'
__url__ = 'https://github.com/pybel/pybel'

__author__ = 'Charles Tapley Hoyt, Andrej Konotopez, Christian Ebeling'
__email__ = 'charles.hoyt@scai.fraunhofer.de'

__license__ = 'Apache 2.0 License'
__copyright__ = 'Copyright (c) 2016 Charles Tapley Hoyt, Andrej Konotopez, Christian Ebeling'


def print_version():
    """Convenience function for printing the PyBEL version"""
    print('{} Version: {}'.format(__title__, __version__))
