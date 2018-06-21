# -*- coding: utf-8 -*-

"""Exceptions for the :mod:`pybel.struct.pipeline` module."""

__all__ = [
    'MissingPipelineFunctionError',
    'MetaValueError',
    'MissingUniverseError',
]


class MissingPipelineFunctionError(KeyError):
    """Raised when trying to run the pipeline with a function that isn't registered"""


class MetaValueError(ValueError):
    """Raised when getting an invalid meta value."""


class MissingUniverseError(ValueError):
    """Raised when running a universe function without a universe being present."""
