# -*- coding: utf-8 -*-

"""

PyBEL's main data structure is a subclass of :class:`networkx.MultiDiGraph`.

The graph contains metadata for the PyBEL version, the BEL script metadata, the namespace definitions, the
annotation definitions, and the warnings produced in analysis. Like any :mod:`networkx` graph, all attributes of
a given object can be accessed through the :code:`graph` property, like in: :code:`my_graph.graph['my key']`.
Convenient property definitions are given for these attributes.

"""

from . import filters, graph, grouping, mutation, operations, summary
from .filters import *
from .graph import *
from .grouping import *
from .mutation import *
from .operations import *
from .pipeline import Pipeline
from .summary import *

__all__ = (
        graph.__all__ +
        grouping.__all__ +
        operations.__all__ +
        filters.__all__ +
        summary.__all__ +
        mutation.__all__ +
        ['Pipeline']
)
