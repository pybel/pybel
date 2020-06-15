# -*- coding: utf-8 -*-

"""Functions for collapsing nodes."""

from . import collapse, protein_rna_origins
from .collapse import *
from .protein_rna_origins import *

__all__ = [k for k in locals() if not k.startswith('_')]
