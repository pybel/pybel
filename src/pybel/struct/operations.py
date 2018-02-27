# -*- coding: utf-8 -*-

import warnings

from .graph import left_full_join, left_node_intersection_join, left_outer_join, node_intersection, union

__all__ = [
    'left_full_join',
    'left_outer_join',
    'union',
    'left_node_intersection_join',
    'node_intersection',
]

warnings.warn('Operations are moved from pybel.struct.operations to pybel.struct.graph', DeprecationWarning)
