# -*- coding: utf-8 -*-

"""Functions for collapsing nodes."""

from . import collapse, protein_rna_origins
from .collapse import *
from .protein_rna_origins import *

__all__ = (
    protein_rna_origins.__all__ +
    collapse.__all__
)
