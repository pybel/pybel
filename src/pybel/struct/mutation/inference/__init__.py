"""Mutations for inferring new edges in the graph."""

from .protein_rna_origins import (
    enrich_proteins_with_rnas,
    enrich_rnas_with_genes,
    enrich_protein_and_rna_origins,
)
from .transfer import infer_child_relations

__all__ = [
    "enrich_protein_and_rna_origins",
    "enrich_proteins_with_rnas",
    "enrich_rnas_with_genes",
    "infer_child_relations",
]
