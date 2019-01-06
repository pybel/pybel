# -*- coding: utf-8 -*-

"""Shared utilities for reading BEL namespace and annotation files."""

import logging
import os
from configparser import ConfigParser
from typing import Dict, Iterable, List, Tuple

import requests.exceptions

from .exc import EmptyResourceError, InvalidResourceError, MissingResourceError
from .utils import download, is_url

__all__ = [
    'parse_bel_resource',
    'get_lines',
    'get_bel_resource',
]

log = logging.getLogger(__name__)


def get_bel_resource(location: str) -> Dict:
    """Load, download, and parse a config file from the given url or file path.

    :param location: The URL or file path to a BELNS, BELANNO, or BELEQ file to download and parse
    :return: A config-style dictionary representing the BEL config file
    :raises: ResourceError
    """
    log.debug('getting resource: %s', location)

    try:
        lines = get_lines(location)
    except requests.exceptions.HTTPError as e:
        raise MissingResourceError(location) from e

    try:
        result = parse_bel_resource(lines)
    except ValueError as e:
        raise InvalidResourceError(location) from e

    if not result['Values']:
        raise EmptyResourceError(location)

    return result


def parse_bel_resource(lines: Iterable[str]) -> Dict:
    """Parse a BEL config (BELNS, BELANNO, or BELEQ) file from the given line iterator over the file.

    :param lines: An iterable over the lines in a BEL config file
    :return: A config-style dictionary representing the BEL config file
    """
    lines = list(lines)

    value_line = 1 + max(
        index
        for index, line in enumerate(lines)
        if '[Values]' == line.strip()
    )

    metadata_config = ConfigParser(strict=False)
    metadata_config.optionxform = lambda option: option
    metadata_config.read_file(lines[:value_line])

    delimiter = metadata_config['Processing']['DelimiterString']

    value_dict = dict(
        _get_bel_resource_kvp(line, delimiter)
        for line in lines[value_line:]
    )

    res = {
        key: dict(values)
        for key, values in metadata_config.items()
    }
    res['Values'] = value_dict

    return res


def _get_bel_resource_kvp(line: str, delimiter: str) -> Tuple[str, str]:
    """Get a BEL resource key/value pair."""
    split_line = line.rsplit(delimiter, 1)
    key = split_line[0].strip()
    value = split_line[1].strip() if 2 == len(split_line) else None
    return key, value


def get_lines(location: str) -> List[str]:
    """Get the lines from a location.

    :param location: The URL location to download or a file path to open. File path expands user.
    :raises: requests.exceptions.HTTPError
    """
    if is_url(location):
        res = download(location)
        return list(line.decode('utf-8', errors='ignore').strip() for line in res.iter_lines())
    else:
        with open(os.path.expanduser(location)) as f:
            return list(f)
