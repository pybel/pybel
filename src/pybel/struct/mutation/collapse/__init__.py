# -*- coding: utf-8 -*-

"""Functions for collapsing nodes."""

from . import protein_rna_origins, collapse
from .protein_rna_origins import *
from .collapse import *

__all__ = (
        protein_rna_origins.__all__ +
        collapse.__all__
)
