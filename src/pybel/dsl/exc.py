# -*- coding: utf-8 -*-

"""Exceptions for the internal DSL."""

from ..exceptions import PyBELWarning

__all__ = [
    'PyBELDSLException',
    'InferCentralDogmaException',
    'ListAbundanceEmptyException',
    'ReactionEmptyException',
]


class PyBELDSLException(PyBELWarning, ValueError):
    """Raised when problems with the DSL."""


class InferCentralDogmaException(PyBELDSLException):
    """Raised when unable to infer central dogma."""


class ListAbundanceEmptyException(PyBELDSLException):
    """Raised when a list abundance has no members."""


class ReactionEmptyException(PyBELDSLException):
    """Raised when a reaction has neither reactants nor products."""
