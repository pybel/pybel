"""Types for PyBEL."""

from collections.abc import Iterable, Mapping
from typing import Union

__all__ = [
    "EdgeData",
    "Strings",
]

Strings = Union[str, Iterable[str]]

EdgeData = Mapping
