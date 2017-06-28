# -*- coding: utf-8 -*-

"""

This module contains functions for filtering node and edge iterables. It relies heavily on the concepts of
`functional programming <https://en.wikipedia.org/wiki/Functional_programming>`_ and the concept of
`predicates <https://en.wikipedia.org/wiki/Predicate_(mathematical_logic)>`_.

"""

from . import edge_filters
from . import node_filters
from .edge_filters import *
from .node_filters import *

__all__ = (
    node_filters.__all__ +
    edge_filters.__all__
)
