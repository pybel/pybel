# -*- coding: utf-8 -*-

"""Warnings for old TSV conversion module."""

import warnings

from ..triples import to_edgelist, to_triples_file as to_tsv

__all__ = [
    'to_tsv',
    'to_edgelist',
]

warnings.warn(
    '''Use pybel.io.triples module instead. Changes in PyBEL v0.15.0:

  - pybel.to_tsv renamed to pybel.to_triples_file

Will be removed in PyBEL v0.16.*
  ''',
    DeprecationWarning,
)
