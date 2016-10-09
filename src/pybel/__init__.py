"""A Python package for parsing, validating, and analysis of of BEL graphs"""

from . import cli
from .graph import BELGraph, from_path, from_lines, from_url, from_database

__all__ = ['from_url', 'from_path', 'from_lines', 'from_database']

__version__ = '0.1.0'

__title__ = 'PyBEL'
__description__ = 'A Python package for parsing, validating, and analysis of of BEL graphs'
__url__ = 'https://github.com/cthoyt/pybel'

__author__ = 'Charles Tapley Hoyt'
__email__ = 'charles.hoyt@scai.fraunhofer.de'

__license__ = 'All Rights Reserved.'
__copyright__ = 'Copyright (c) Charles Tapley Hoyt'
