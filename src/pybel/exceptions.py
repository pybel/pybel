# -*- coding: utf-8 -*-

"""This module contains base exceptions that are shared through the package."""


class PyBelWarning(Exception):
    """The base class for warnings during compilation from which PyBEL can recover."""


class PyBELCanonicalizeError(PyBelWarning, IndexError):
    """Raised when problem canonicalizing a node."""
