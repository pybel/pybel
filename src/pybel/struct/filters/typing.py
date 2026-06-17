"""Types for filters."""

from collections.abc import Callable, Iterable
from typing import Union

from ..graph import BELGraph
from ...dsl import BaseEntity

__all__ = [
    "EdgeIterator",
    "EdgePredicate",
    "EdgePredicates",
    "EdgeTuple",
    "NodePredicate",
    "NodePredicates",
]

NodePredicate = Callable[[BELGraph, BaseEntity], bool]
NodePredicates = Union[NodePredicate, Iterable[NodePredicate]]

EdgeTuple = tuple[BaseEntity, BaseEntity, str]
EdgeIterator = Iterable[EdgeTuple]

EdgePredicate = Callable[[BELGraph, BaseEntity, BaseEntity, str], bool]
EdgePredicates = Union[EdgePredicate, Iterable[EdgePredicate]]
