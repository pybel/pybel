"""Functions for grouping BEL graphs into sub-graphs."""

from .annotations import get_subgraphs_by_annotation
from .provenance import get_subgraphs_by_citation

__all__ = [
    "get_subgraphs_by_annotation",
    "get_subgraphs_by_citation",
]
