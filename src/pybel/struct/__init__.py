# -*- coding: utf-8 -*-

"""The :mod:`pybel.struct` module houses functions for handling the main data structure in PyBEL.

Because BEL expresses how biological entities interact within many
different contexts, with descriptive annotations, PyBEL represents data as a directed multi-graph by sub-classing the
:class:`networkx.MultiDiGraph`. Each node is an instance of a subclass of the :class:`pybel.dsl.BaseEntity` and each
edge has a stable key and associated data dictionary for storing relevant contextual information.

The graph contains metadata for the PyBEL version, the BEL script metadata, the namespace definitions, the
annotation definitions, and the warnings produced in analysis. Like any :mod:`networkx` graph, all attributes of
a given object can be accessed through the :code:`graph` property, like in: :code:`my_graph.graph['my key']`.
Convenient property definitions are given for these attributes that are outlined in the documentation for
:class:`pybel.BELGraph`.

This allows for much easier programmatic access to answer more complicated questions, which can be written with python
code. Because the data structure is the same in Neo4J, the data can be directly exported with :func:`pybel.to_neo4j`.
Neo4J supports the Cypher querying language so that the same queries can be written in an elegant and simple way.
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
