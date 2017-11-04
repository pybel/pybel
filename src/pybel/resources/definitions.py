# -*- coding: utf-8 -*-

import hashlib
import json
import logging
import os
from collections import Iterable
from configparser import ConfigParser

from .exc import EmptyResourceError, MissingSectionError
from .utils import download, is_url

log = logging.getLogger(__name__)


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


def names_to_bytes(names):
    """Reproducibly converts an iterable of strings to bytes

    :param iter[str] names: An iterable of strings
    :rtype: bytes
    """
    names = sorted(names)
    names_bytes = json.dumps(names).encode('utf8')
    return names_bytes


def hash_names(names, hash_function=None):
    """Returns the hash of an iterable of strings, or a dict if multiple hash functions given.

    :param iter[str] names: An iterable of strings
    :param hash_function: A hash function or list of hash functions, like :func:`hashlib.md5` or :func:`hashlib.sha512`
    :rtype: str
    """
    names_bytes = names_to_bytes(names)

    if hash_function is None:
        hash_function = hashlib.md5

    if isinstance(hash_function, Iterable):
        return {
            hf.__name__: hf(names_bytes).hexdigest()
            for hf in hash_function
        }

    return hash_function(names_bytes).hexdigest()


def hash_bel_resource(file, hash_function=None):
    """Semantically hashes a BEL resource file

    :param file file: A readable file or file-like
    :param hash_function: A hash function or list of hash functions, like :func:`hashlib.md5` or :code:`hashlib.sha512`
    :rtype: str
    """
    resource = parse_bel_resource(file)

    return hash_names(
        resource['Values'],
        hash_function=hash_function
    )


def get_bel_resource_hash(location, hash_function=None):
    """Gets a BEL resource file and returns its semantic hash

    :param str location: URL of a resource
    :param hash_function: A hash function or list of hash functions, like :func:`hashlib.md5` or :code:`hashlib.sha512`
    :return: The hexadecimal digest of the hash of the values in the resource
    :rtype: str
    """
    resource = get_bel_resource(location)

    return hash_names(
        resource['Values'],
        hash_function=hash_function
    )


def check_cacheable(config):
    """Checks the config returned by :func:`pybel.utils.get_bel_resource` to determine if the resource should be cached.

    If cannot be determined, returns ``False``

    :param dict config: A configuration dictionary representing a BEL resource
    :return: Should this resource be cached
    :rtype: bool
    """

    if 'Processing' in config and 'CacheableFlag' in config['Processing']:
        flag = config['Processing']['CacheableFlag']

        if 'yes' == flag:
            return True
        elif 'no' == flag:
            return False
        else:
            return ValueError('Invalid value for CacheableFlag: {}'.format(flag))

    return False
