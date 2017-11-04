# -*- coding: utf-8 -*-

import logging
import os
from configparser import ConfigParser

import requests
from requests.compat import urlparse
from requests_file import FileAdapter

from .constants import BELFRAMEWORK_DOMAIN, OPENBEL_DOMAIN
from .exc import EmptyResourceError, MissingSectionError

log = logging.getLogger(__name__)


def download(url):
    """Uses requests to download an URL, maybe from a file"""
    session = requests.Session()
    session.mount('file://', FileAdapter())

    if url.startswith(BELFRAMEWORK_DOMAIN):
        url = url.replace(BELFRAMEWORK_DOMAIN, OPENBEL_DOMAIN)
        log.warning('%s has expired. Redirecting to %s', BELFRAMEWORK_DOMAIN, url)

    try:
        res = session.get(url)
    except requests.exceptions.ConnectionError as e:
        raise e

    res.raise_for_status()
    return res


def get_bel_resource_kvp(line, delimiter):
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

    value_line = 1 + max(i for i, line in enumerate(lines) if '[Values]' == line.strip())

    metadata_config = ConfigParser(strict=False)
    metadata_config.optionxform = lambda option: option
    metadata_config.read_file(lines[:value_line])

    delimiter = metadata_config['Processing']['DelimiterString']

    value_dict = dict(
        get_bel_resource_kvp(line, delimiter)
        for line in lines[value_line:]
    )

    res = {}
    res.update({k: dict(v) for k, v in metadata_config.items()})
    res['Values'] = value_dict

    return res


def is_url(s):
    """Checks if a string is a valid URL

    :param str s: An input string
    :return: Is the string a valid URL?
    :rtype: bool
    """
    return urlparse(s).scheme != ""


def get_lines(location):
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
    """
    lines = get_lines(location)

    try:
        result = parse_bel_resource(lines)
    except ValueError:
        log.error('No [Values] section found in %s', location)
        raise MissingSectionError(location)

    if not result['Values']:
        raise EmptyResourceError(location)

    return result
