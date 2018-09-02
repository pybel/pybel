# -*- coding: utf-8 -*-

"""This module contains simple wrappers around node DSL functions for common namespaces."""

from .nodes import Abundance, Protein

__all__ = [
    'chebi',
    'hgnc',
]


def chebi(name=None, identifier=None):
    """Build a ChEBI abundance node."""
    return Abundance(namespace='CHEBI', name=name, identifier=identifier)


def hgnc(name=None, identifier=None):
    """Build an HGNC protein node."""
    return Protein(namespace='HGNC', name=name, identifier=identifier)
