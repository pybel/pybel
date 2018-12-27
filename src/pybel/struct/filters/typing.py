# -*- coding: utf-8 -*-

"""Types for filters."""

from typing import Callable, Iterable, Tuple, Union

from ..graph import BELGraph
from ...dsl import BaseEntity

__all__ = [
    'NodePredicate',
    'NodePredicates',
    'EdgeTuple',
    'EdgeIterator',
    'EdgePredicate',
    'EdgePredicates',
]

NodePredicate = Callable[[BELGraph, BaseEntity], bool]
NodePredicates = Union[NodePredicate, Iterable[NodePredicate]]

EdgeTuple = Tuple[BaseEntity, BaseEntity, str]
EdgeIterator = Iterable[EdgeTuple]

EdgePredicate = Callable[[BELGraph, BaseEntity, BaseEntity, str], bool]
EdgePredicates = Union[EdgePredicate, Iterable[EdgePredicate]]
