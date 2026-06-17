"""Type hints for the parsers."""

from collections.abc import Mapping

__all__ = [
    "NamespaceTermEncodingMapping",
    "Term",
    "TermEncodingMapping",
]

Term = tuple[str | None, str]
TermEncodingMapping = Mapping[Term, str]
NamespaceTermEncodingMapping = Mapping[str, Mapping[Term, str]]
