# -*- coding: utf-8 -*-

"""Exceptions for the :mod:`pybel.struct.pipeline` module."""

__all__ = [
    'MissingPipelineFunctionError',
]


class MissingPipelineFunctionError(KeyError):
    """Raised when trying to run the pipeline with a function that isn't registered"""
