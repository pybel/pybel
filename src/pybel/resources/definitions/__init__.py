# -*- coding: utf-8 -*-

"""Functions for reading and writing BEL namespace and annotation files."""

from . import annotation, definitions, namespace, write_utils
from .annotation import *
from .definitions import *
from .namespace import *

__all__ = (
    definitions.__all__ +
    annotation.__all__ +
    namespace.__all__
)
