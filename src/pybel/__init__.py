"""Parsing, validation, and analysis of of BEL graphs"""

from __future__ import print_function

from . import cli
from . import graph
from .graph import *

__all__ = graph.__all__

__version__ = '0.2.3'

__title__ = 'PyBEL'
__description__ = 'Parsing, validation, and analysis of BEL graphs'
__url__ = 'https://github.com/pybel/pybel'

__author__ = 'Charles Tapley Hoyt, Andrej Konotopez, Christian Ebeling'
__email__ = 'charles.hoyt@scai.fraunhofer.de'

__license__ = 'Apache 2.0 License'
__copyright__ = 'Copyright (c) 2016 Charles Tapley Hoyt, Andrej Konotopez, Christian Ebeling'


def version():
    print('{} Version: {}'.format(__title__, __version__))
