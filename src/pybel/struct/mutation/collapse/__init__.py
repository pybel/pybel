# -*- coding: utf-8 -*-

"""Functions for collapsing nodes."""

from . import central_dogma, collapse
from .central_dogma import *
from .collapse import *

__all__ = (
        central_dogma.__all__ +
        collapse.__all__
)
