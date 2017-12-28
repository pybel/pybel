# -*- coding: utf-8 -*-

from ..exceptions import PyBelWarning


class PyBELDSLException(PyBelWarning, ValueError):
    """Raised when problems with the DSL"""
