"""This module contains simple wrappers around node DSL functions for common namespaces."""

from .node_classes import Abundance, MicroRna, Protein

__all__ = [
    "chebi",
    "hgnc",
    "mirbase",
]


def chebi(*, name: str | None = None, identifier: str | None = None) -> Abundance:
    """Build a ChEBI abundance node."""
    return Abundance(namespace="CHEBI", name=name, identifier=identifier)


def hgnc(*, name: str | None = None, identifier: str | None = None) -> Protein:
    """Build an HGNC protein node."""
    return Protein(namespace="HGNC", name=name, identifier=identifier)


def mirbase(*, name: str | None = None, identifier: str | None = None) -> MicroRna:
    """Build an miRBase micro-rna node."""
    return MicroRna(namespace="MIRBASE", name=name, identifier=identifier)
