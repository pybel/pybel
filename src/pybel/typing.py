# -*- coding: utf-8 -*-

"""Types for PyBEL."""

from typing import Iterable, Mapping, Union

__all__ = [
    'Strings',
    'EdgeData',
]

Strings = Union[str, Iterable[str]]

EdgeData = Mapping
