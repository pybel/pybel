# -*- coding: utf-8 -*-

"""This module contains simple wrappers around node DSL functions for common namespaces."""

from .nodes import abundance, protein


def chebi(name=None, identifier=None):
    return abundance(namespace='CHEBI', name=name, identifier=identifier)


def hgnc(name=None, identifier=None):
    return protein(namespace='HGNC', name=name, identifier=identifier)
