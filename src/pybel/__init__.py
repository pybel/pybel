"""Parsing, validation, and analysis of of BEL graphs"""

from . import graph
from . import io
from .canonicalize import to_bel
from .graph import *
from .io import *
from .manager import to_database, from_database

__all__ = ['to_database', 'from_database', 'to_bel'] + graph.__all__ + io.__all__

__version__ = '0.3.5-dev'

__title__ = 'PyBEL'
__description__ = 'Parsing, validation, and analysis of BEL graphs'
__url__ = 'https://github.com/pybel/pybel'

__author__ = 'Charles Tapley Hoyt, Andrej Konotopez, Christian Ebeling'
__email__ = 'charles.hoyt@scai.fraunhofer.de'

__license__ = 'Apache 2.0 License'
__copyright__ = 'Copyright (c) 2016 Charles Tapley Hoyt, Andrej Konotopez, Christian Ebeling'
