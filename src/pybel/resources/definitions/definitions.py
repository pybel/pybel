# -*- coding: utf-8 -*-

import logging
import os
import requests.exceptions
import six
from configparser import ConfigParser

from ..exc import EmptyResourceError, InvalidResourceError, MissingResourceError
from ..utils import download, is_url

__all__ = [
    'parse_bel_resource',
    'get_lines',
    'get_bel_resource',
]

log = logging.getLogger(__name__)


def _get_bel_resource_kvp(line, delimiter):
    """

    :param str line:
    :param str delimiter:
    :rtype: tuple[str,str]
    """
    split_line = line.rsplit(delimiter, 1)
    key = split_line[0].strip()
    value = split_line[1].strip() if 2 == len(split_line) else None
    return key, value


def parse_bel_resource(lines):
    """Parses a BEL config (BELNS, BELANNO, or BELEQ) file from the given line iterator over the file

    :param iter[str] lines: An iterable over the lines in a BEL config file
    :return: A config-style dictionary representing the BEL config file
    :rtype: dict
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

    res = {}
    res.update({k: dict(v) for k, v in metadata_config.items()})
    res['Values'] = value_dict

    return res


def get_lines(location):
    """Gets the lines from a location

    :param str location: The URL location to download or a file path to open. File path expands user.
    :return: list[str]
    :raises: requests.exceptions.HTTPError
    """
    if is_url(location):
        res = download(location)
        return list(line.decode('utf-8', errors='ignore').strip() for line in res.iter_lines())
    else:
        with open(os.path.expanduser(location)) as f:
            return list(f)


def get_bel_resource(location):
    """Loads/downloads and parses a config file from the given url or file path

    :param str location: The URL or file path to a BELNS, BELANNO, or BELEQ file to download and parse
    :return: A config-style dictionary representing the BEL config file
    :rtype: dict
    :raises: pybel.resources.exc.ResourceError
    """
    log.debug('getting resource: %s', location)

    try:
        lines = get_lines(location)
    except requests.exceptions.HTTPError as e:
        six.raise_from(MissingResourceError(location), e)

    try:
        result = parse_bel_resource(lines)
    except ValueError as e:
        six.raise_from(InvalidResourceError(location), e)

    if not result['Values']:
        raise EmptyResourceError(location)

    return result
