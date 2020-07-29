# -*- coding: utf-8 -*-

"""Warnings for old TSV conversion module."""

import warnings

from ..triples.converters import _safe_label

__all__ = [
    '_safe_label',
]

warnings.warn(
    '''Use pybel.io.triples module instead. Changes in PyBEL v0.15.0:

  - pybel.io.tsv.converters._safe_label renamed to pybel.io.triples.converters._safe_label

Will be removed in PyBEL v0.16.*
  ''',
    DeprecationWarning,
)
