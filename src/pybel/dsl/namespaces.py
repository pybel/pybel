# -*- coding: utf-8 -*-

"""This module contains simple wrappers around node DSL functions for common namespaces."""

from typing import Optional

from .node_classes import Abundance, MicroRna, Protein

__all__ = [
    'chebi',
    'hgnc',
    'mirbase',
]


def chebi(*, name: Optional[str] = None, identifier: Optional[str] = None) -> Abundance:
    """Build a ChEBI abundance node."""
    return Abundance(namespace='CHEBI', name=name, identifier=identifier)


def hgnc(*, name: Optional[str] = None, identifier: Optional[str] = None) -> Protein:
    """Build an HGNC protein node."""
    return Protein(namespace='HGNC', name=name, identifier=identifier)


def mirbase(*, name: Optional[str] = None, identifier: Optional[str] = None) -> MicroRna:
    """Build an miRBase micro-rna node."""
    return MicroRna(namespace='MIRBASE', name=name, identifier=identifier)
