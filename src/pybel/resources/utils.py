# -*- coding: utf-8 -*-

"""Utilities for reading and writing BEL script, namespace files, and annotation files."""

import requests
import time
from requests.compat import urlparse
from requests_file import FileAdapter

__all__ = [
    'get_iso_8601_date',
    'is_url',
    'download',
]


def get_iso_8601_date():
    """Get the current date as a string in YYYYMMDD format.

    :rtype: str
    """
    return time.strftime('%Y%m%d')


def is_url(s):
    """Check if a string is a valid URL.

    :param str s: An input string
    :return: Is the string a valid URL?
    :rtype: bool
    """
    return urlparse(s).scheme != ""


def download(url):
    """Download an URL or file using :py:mod:`requests`.

    :param str url: The URL to download
    :rtype: requests.Response
    :raises: requests.exceptions.HTTPError
    """
    session = requests.Session()
    session.mount('file://', FileAdapter())

    res = session.get(url)
    res.raise_for_status()

    return res
