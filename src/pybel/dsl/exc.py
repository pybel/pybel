# -*- coding: utf-8 -*-

"""Exceptions for the internal DSL."""

from ..exceptions import PyBelWarning

__all__ = [
    'PyBELDSLException',
    'InferCentralDogmaException',
]


class PyBELDSLException(PyBelWarning, ValueError):
    """Raised when problems with the DSL."""


class InferCentralDogmaException(PyBELDSLException):
    """Raised when unable to infer central dogma."""
