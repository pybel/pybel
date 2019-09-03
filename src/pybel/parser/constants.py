# -*- coding: utf-8 -*-

"""Type hints for the parsers."""

from typing import Mapping, Optional, Tuple

__all__ = [
    'Term',
    'TermEncodingMapping',
    'NamespaceTermEncodingMapping',
]

Term = Tuple[Optional[str], str]
TermEncodingMapping = Mapping[Term, str]
NamespaceTermEncodingMapping = Mapping[str, Mapping[Term, str]]
