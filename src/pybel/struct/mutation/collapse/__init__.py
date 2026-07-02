"""Functions for collapsing nodes."""

from .collapse import (
    collapse_all_variants,
    collapse_nodes,
    collapse_pair,
    surviors_are_inconsistent,
)
from .protein_rna_origins import collapse_to_genes

__all__ = [
    "collapse_all_variants",
    "collapse_nodes",
    "collapse_to_genes",
    "collapse_pair",
    "surviors_are_inconsistent",
]
