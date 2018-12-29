# -*- coding: utf-8 -*-

"""Utilities for reading and writing BEL script, namespace files, and annotation files."""

import time
from urllib.parse import urlparse

import requests
from requests_file import FileAdapter

__all__ = [
    'get_iso_8601_date',
    'is_url',
    'download',
]


def get_iso_8601_date() -> str:
    """Get the current date as a string in YYYYMMDD format."""
    return time.strftime('%Y%m%d')


def is_url(s: str) -> bool:
    """Check if a string is a valid URL."""
    return urlparse(s).scheme != ""


def download(url: str) -> requests.Response:
    """Download an URL or file using :py:mod:`requests`.

    :raises: requests.exceptions.HTTPError
    """
    session = requests.Session()
    session.mount('file://', FileAdapter())

    res = session.get(url)
    res.raise_for_status()

    return res
