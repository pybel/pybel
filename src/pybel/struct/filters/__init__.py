# -*- coding: utf-8 -*-

"""This module contains functions for filtering node and edge iterables.

It relies heavily on the concepts of `functional programming <https://en.wikipedia.org/wiki/Functional_programming>`_
and the concept of `predicates <https://en.wikipedia.org/wiki/Predicate_(mathematical_logic)>`_.
"""

from . import (
    edge_filters, edge_predicate_builders, edge_predicates, node_filters, node_predicate_builders, node_predicates,
    node_selection, utils,
)
from .edge_filters import *
from .edge_predicate_builders import *
from .edge_predicates import *
from .node_filters import *
from .node_predicate_builders import *
from .node_predicates import *
from .node_selection import *
from .utils import *

__all__ = (
        edge_filters.__all__ +
        edge_predicates.__all__ +
        edge_predicate_builders.__all__ +
        node_filters.__all__ +
        node_predicate_builders.__all__ +
        node_predicates.__all__ +
        node_selection.__all__ +
        utils.__all__
)
