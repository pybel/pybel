"""Exceptions for the query builder."""

__all__ = [
    "NodeDegreeIterError",
    "QueryMissingNetworksError",
]


class QueryMissingNetworksError(KeyError):
    """Raised if a query is created from json but doesn't have a listing of network identifiers."""


class NodeDegreeIterError(ValueError):
    """Raised when failing to iterate over node degrees."""
