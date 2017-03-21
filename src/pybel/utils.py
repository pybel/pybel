# -*- coding: utf-8 -*-

import itertools as itt
import logging
from collections import defaultdict, MutableMapping
from configparser import ConfigParser
from datetime import datetime
from operator import itemgetter

import networkx as nx
import requests
from pkg_resources import get_distribution
from requests_file import FileAdapter

from pybel.constants import CITATION_ENTRIES, CITATION, EVIDENCE, ANNOTATIONS

log = logging.getLogger('pybel')


def download_url(url):
    """Downloads and parses a config file from url

    :param url: the URL of a BELNS, BELANNO, or BELEQ file to download and parse
    :type url: str
    """
    session = requests.Session()
    session.mount('file://', FileAdapter())
    res = session.get(url)

    lines = [line.decode('utf-8', errors='ignore').strip() for line in res.iter_lines()]

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

    if not value_dict:
        raise ValueError('Downloaded empty file: {}'.format(url))

    res = {}
    res.update({k: dict(v) for k, v in metadata_config.items()})
    res['Values'] = value_dict

    return res


def expand_dict(flat_dict, sep='_'):
    """Expands a flattened dictionary

    :param flat_dict: a nested dictionary that has been flattened so the keys are composite
    :type flat_dict: dict
    :param sep: the separator between concatenated keys
    :type sep: str
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
    :param parent_key: The parent's key. This is a value for tail recursion, so don't set it yourself.
    :type parent_key: str
    :param sep: The separator used between dictionary levels
    :type sep: str

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
    """Returns a new graph with flattened edge data dictionaries

    :param graph:
    :type graph: nx.MultiDiGraph
    :rtype: nx.MultiDiGraph
    """

    g = nx.MultiDiGraph()

    for node, data in graph.nodes(data=True):
        g.add_node(node, data)

    for u, v, key, data in graph.edges(data=True, keys=True):
        g.add_edge(u, v, key=key, attr_dict=flatten_dict(data))

    return g


def list2tuple(l):
    """turns a nested list to a nested tuple"""
    if isinstance(l, list):
        return tuple(list2tuple(e) for e in l)
    else:
        return l


def get_version():
    return get_distribution('pybel').version


def tokenize_version(version_string):
    return tuple(map(int, version_string.split('.')[0:3]))


def citation_dict_to_tuple(citation):
    return tuple(citation[x] for x in CITATION_ENTRIES[:len(citation)])


def flatten_citation(citation):
    return ','.join('"{}"'.format(e) for e in citation_dict_to_tuple(citation))


def sort_edges(d):
    return (flatten_citation(d[CITATION]), d[EVIDENCE]) + tuple(
        itt.chain.from_iterable(sorted(d[ANNOTATIONS].items(), key=itemgetter(0))))


def ensure_quotes(s):
    """Quote a string that isn't solely alphanumeric

    :param s: a string
    :type s: str
    :rtype: str
    """
    return '"{}"'.format(s) if not s.isalnum() else s


CREATION_DATE_FMT = '%Y-%m-%dT%H:%M:%S'
PUBLISHED_DATE_FMT = '%Y-%m-%d'
PUBLISHED_DATE_FMT_2 = '%d:%m:%Y %H:%M'


def valid_date(s):
    """Checks that a string represents a valid date in ISO 8601 format YYYY-MM-DD"""
    try:
        datetime.strptime(s, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def parse_datetime(s):
    """Tries to parse a datetime object from a standard datetime format or date format

    :param s: A string represing a date or datetime
    :type s: str
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

    :param x: A BEL node
    :type x: tuple
    :return: A hashed version of the node tuple
    :rtype: int
    """
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

    :param target: The dictionary to search
    :type target: dict
    :param query: A query dict with keys to match
    :type query: dict
    :param partial_match: Should the query values be used as partial or exact matches? Defaults to :code:`True`.
    :type partial_match: bool
    :return: if all keys in b are in target_dict and their values match
    :rtype: bool
    """
    for k, v in query.items():
        if k not in target:
            return False
        elif not isinstance(v, (str, list, set, dict, tuple)):
            raise ValueError('invalid value: {}'.format(v))
        elif isinstance(v, str) and target[k] != v:
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
