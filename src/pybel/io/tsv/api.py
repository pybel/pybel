# -*- coding: utf-8 -*-

"""Warnings for old TSV conversion module."""

import warnings

from ..triples.api import to_triple as get_triple, to_triples as get_triples

__all__ = [
    'get_triple',
    'get_triples',
]

warnings.warn(
    '''Use pybel.io.triples module instead. Changes in PyBEL v0.15.0:

  - pybel.io.tsv.api.get_triples renamed to pybel.to_triples
  - pybel.io.tsv.api.get_triple renamed to pybel.io.triples.to_triple

Will be removed in PyBEL v0.16.*
  ''',
    DeprecationWarning,
)
