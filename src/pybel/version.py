# -*- coding: utf-8 -*-

"""The current version of PyBEL."""

__all__ = [
    'VERSION',
    'get_version',
]

VERSION = '0.14.6-dev'


def get_version() -> str:
    """Get the current PyBEL software version."""
    return VERSION
