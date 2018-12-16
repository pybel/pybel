# -*- coding: utf-8 -*-

"""Exceptions for the :mod:`pybel.struct.pipeline` module."""

__all__ = [
    'MissingPipelineFunctionError',
    'MetaValueError',
    'MissingUniverseError',
    'DeprecationMappingError',
    'PipelineNameError',
]


class MissingPipelineFunctionError(KeyError):
    """Raised when trying to run the pipeline with a function that isn't registered."""


class MetaValueError(ValueError):
    """Raised when getting an invalid meta value."""


class MissingUniverseError(ValueError):
    """Raised when running a universe function without a universe being present."""


class DeprecationMappingError(ValueError):
    """Raised when applying the deprecation function annotation and the given name already is being used."""


class PipelineNameError(ValueError):
    """Raised when a second function tries to use the same name."""
