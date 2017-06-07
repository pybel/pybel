# -*- coding: utf-8 -*-

import itertools as itt
import logging
import os
from collections import defaultdict, MutableMapping
from configparser import ConfigParser
from datetime import datetime
from operator import itemgetter

import networkx as nx
import requests
import requests.exceptions
from pkg_resources import get_distribution
from requests.compat import urlparse
from requests_file import FileAdapter
from six import string_types

from .constants import CITATION_ENTRIES, CITATION, EVIDENCE, ANNOTATIONS, BELFRAMEWORK_DOMAIN, OPENBEL_DOMAIN

log = logging.getLogger(__name__)


def download(url):
    """Uses requests to download an URL, maybe from a file"""
    session = requests.Session()
    session.mount('file://', FileAdapter())

    if url.startswith(BELFRAMEWORK_DOMAIN):
        log.warning('%s has expired', BELFRAMEWORK_DOMAIN)
        url = url.replace(BELFRAMEWORK_DOMAIN, OPENBEL_DOMAIN)

    try:
        res = session.get(url)
    except requests.exceptions.ConnectionError as e:
        raise e

    res.raise_for_status()
    return res


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

    value_dict = {}
    for line in lines[value_line:]:
        sline = line.rsplit(delimiter, 1)
        key = sline[0].strip()

        value_dict[key] = sline[1].strip() if len(sline) == 2 else None

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


def get_bel_resource(location):
    """Loads/downloads and parses a config file from the given url or file path

    :param str location: The URL or file path to a BELNS, BELANNO, or BELEQ file to download and parse
    :return: A config-style dictionary representing the BEL config file
    :rtype: dict
    """

    if is_url(location):
        res = download(location)
        lines = list(line.decode('utf-8', errors='ignore').strip() for line in res.iter_lines())
    else:
        with open(os.path.expanduser(location)) as f:
            lines = list(f)

    try:
        result = parse_bel_resource(lines)
    except ValueError:
        log.error('No [Values] section found in %s', location)
        raise ValueError('No [Values] section found in {}'.format(location))

    if not result['Values']:
        raise ValueError('Downloaded empty file: {}'.format(location))

    return result


def expand_dict(flat_dict, sep='_'):
    """Expands a flattened dictionary

    :param dict flat_dict: a nested dictionary that has been flattened so the keys are composite
    :param str sep: the separator between concatenated keys
    """
    res = {}
    rdict = defaultdict(list)

    for flat_key, value in flat_dict.items():
        key = flat_key.split(sep, 1)
        if 1 == len(key):
            res[key[0]] = value
        else:
            rdict[key[0]].append((key[1:], value))

    for k, v in rdict.items():
        res[k] = expand_dict({ik: iv for (ik,), iv in v})

    return res


def flatten_dict(d, parent_key='', sep='_'):
    """Flattens a nested dictionary.

    :param d: A nested dictionary
    :type d: dict or MutableMapping
    :param str parent_key: The parent's key. This is a value for tail recursion, so don't set it yourself.
    :param str sep: The separator used between dictionary levels

    .. seealso:: http://stackoverflow.com/a/6027615
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, (dict, MutableMapping)):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, (set, list)):
            items.append((new_key, ','.join(v)))
        else:
            items.append((new_key, v))
    return dict(items)


def flatten_graph_data(graph):
    """Returns a new graph with flattened edge data dictionaries.

    :param nx.MultiDiGraph graph: A graph with nested edge data dictionaries
    :return: A graph with flattened edge data dictionaries
    :rtype: nx.MultiDiGraph
    """
    g = nx.MultiDiGraph(**graph.graph)

    for node, data in graph.nodes(data=True):
        g.add_node(node, data)

    for u, v, key, data in graph.edges(data=True, keys=True):
        g.add_edge(u, v, key=key, attr_dict=flatten_dict(data))

    return g


def list2tuple(l):
    """Recursively converts a nested list to a nested tuple"""
    if isinstance(l, list):
        return tuple(list2tuple(e) for e in l)
    else:
        return l


def get_version():
    """Gets the current PyBEL version
    
    :return: The current PyBEL version
    :rtype: str
    """
    return get_distribution('pybel').version


def tokenize_version(version_string):
    """Tokenizes a version string to a tuple. Truncates qualifiers like ``-dev``.

    :param str version_string: A version string
    :return: A tuple representing the version string
    :rtype: tuple

    >>> tokenize_version('0.1.2-dev')
    (0, 1, 2)

    """
    return tuple(map(int, version_string.split('.')[0:3]))


def citation_dict_to_tuple(citation):
    """Convert the ``d[CITATION]`` entry in an edge data dictionary to a tuple"""
    if all(x in citation for x in CITATION_ENTRIES):
        return tuple(citation[x] for x in CITATION_ENTRIES)

    if all(x in citation for x in CITATION_ENTRIES[3:5]):
        return tuple(citation[x] for x in CITATION_ENTRIES[:5])

    if all(x in citation for x in CITATION_ENTRIES[3:4]):
        return tuple(citation[x] for x in CITATION_ENTRIES[:4])

    return tuple(citation[x] for x in CITATION_ENTRIES[:3])


def flatten_citation(citation):
    """Flattens a citation dict, from the ``d[CITATION]`` entry in an edge data dictionary"""
    return ','.join('"{}"'.format(e) for e in citation_dict_to_tuple(citation))


def sort_edges(d):
    """Acts as a sort key function for an edge"""
    return (flatten_citation(d[CITATION]), d[EVIDENCE]) + tuple(
        itt.chain.from_iterable(sorted(d[ANNOTATIONS].items(), key=itemgetter(0))))


def ensure_quotes(s):
    """Quote a string that isn't solely alphanumeric

    :param str s: a string
    :rtype: str
    """
    return '"{}"'.format(s) if not s.isalnum() else s


CREATION_DATE_FMT = '%Y-%m-%dT%H:%M:%S'
PUBLISHED_DATE_FMT = '%Y-%m-%d'
PUBLISHED_DATE_FMT_2 = '%d:%m:%Y %H:%M'


def valid_date(s):
    """Checks that a string represents a valid date in ISO 8601 format YYYY-MM-DD
    
    :type s: str
    :rtype: bool
    """
    try:
        datetime.strptime(s, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def valid_date_version(s):
    """Checks that the string is a valid date versions string"""
    try:
        datetime.strptime(s, '%Y%m%d')
        return True
    except ValueError:
        return False


def parse_datetime(s):
    """Tries to parse a datetime object from a standard datetime format or date format

    :param str s: A string representing a date or datetime
    :return: A parsed date object
    :rtype: datetime.date
    """
    try:
        dt = datetime.strptime(s, CREATION_DATE_FMT)
        return dt
    except:
        try:
            dt = datetime.strptime(s, PUBLISHED_DATE_FMT)
            return dt
        except:
            try:
                dt = datetime.strptime(s, PUBLISHED_DATE_FMT_2)
                return dt
            except:
                raise ValueError('Incorrect datetime format for {}'.format(s))


def hash_tuple(x):
    """Converts a PyBEL node tuple to a hash

    :param tuple x: A BEL node
    :return: A hashed version of the node tuple
    :rtype: int
    """
    if isinstance(x, int):
        return x

    h = 0
    for i in x:
        if isinstance(i, tuple):
            h += hash_tuple(i)
        else:
            h += hash(i)
    return hash(h)


def subdict_matches(target, query, partial_match=True):
    """Checks if all the keys in the query dict are in the target dict, and that their values match

    1. Checks that all keys in the query dict are in the target dict
    2. Matches the values of the keys in the query dict
        a. If the value is a string, then must match exactly
        b. If the value is a set/list/tuple, then will match any of them
        c. If the value is a dict, then recursively check if that subdict matches

    :param dict target: The dictionary to search
    :param dict query: A query dict with keys to match
    :param bool partial_match: Should the query values be used as partial or exact matches? Defaults to :code:`True`.
    :return: if all keys in b are in target_dict and their values match
    :rtype: bool
    """
    for k, v in query.items():
        if k not in target:
            return False
        elif not isinstance(v, (int, string_types, list, set, dict, tuple)):
            raise ValueError('invalid value: {}'.format(v))
        elif isinstance(v, (int, string_types)) and target[k] != v:
            return False
        elif isinstance(v, dict):
            if partial_match:
                if not isinstance(target[k], dict):
                    return False
                elif not subdict_matches(target[k], v, partial_match):
                    return False
            elif not partial_match and target[k] != v:
                return False
        elif isinstance(v, (list, set, tuple)) and target[k] not in v:
            return False

    return True
