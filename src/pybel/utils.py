# -*- coding: utf-8 -*-

from collections import Iterable, MutableMapping, defaultdict

import hashlib
import json
import logging
import networkx as nx
import pickle
from datetime import datetime
from six import string_types

from .constants import (
    CITATION_AUTHORS, CITATION_ENTRIES, CITATION_REFERENCE, CITATION_TYPE,
    PYBEL_EDGE_DATA_KEYS, VERSION,
)

log = logging.getLogger(__name__)


def expand_dict(flat_dict, sep='_'):
    """Expands a flattened dictionary

    :param dict flat_dict: a nested dictionary that has been flattened so the keys are composite
    :param str sep: the separator between concatenated keys
    :rtype: dict
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
    :rtype: dict

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
    """Recursively converts a nested list to a nested tuple

    :type l: list
    :rtype: tuple
    """
    if isinstance(l, list):
        return tuple(list2tuple(e) for e in l)
    else:
        return l


def get_version():
    """Gets the current PyBEL version
    
    :return: The current PyBEL version
    :rtype: str
    """
    return VERSION


def tokenize_version(version_string):
    """Tokenizes a version string to a tuple. Truncates qualifiers like ``-dev``.

    :param str version_string: A version string
    :return: A tuple representing the version string
    :rtype: tuple

    >>> tokenize_version('0.1.2-dev')
    (0, 1, 2)

    """
    before_dash = version_string.split('-')[0]
    version_tuple = before_dash.split('.')[:3]  # take only the first 3 in case there's an extension like -dev.0
    return tuple(map(int, version_tuple))


def citation_dict_to_tuple(citation):
    """Convert the ``d[CITATION]`` entry in an edge data dictionary to a tuple

    :param dict citation:
    :rtype: tuple[str]
    """
    if len(citation) == 2 and CITATION_TYPE in citation and CITATION_REFERENCE in citation:
        return citation[CITATION_TYPE], citation[CITATION_REFERENCE]

    if all(x in citation for x in CITATION_ENTRIES):
        return tuple(citation[x] for x in CITATION_ENTRIES)

    if all(x in citation for x in CITATION_ENTRIES[3:5]):
        ff = tuple(citation[x] for x in CITATION_ENTRIES[:4])

        if isinstance(citation[CITATION_AUTHORS], string_types):
            return ff + (citation[CITATION_AUTHORS],)
        else:
            return ff + ('|'.join(citation[CITATION_AUTHORS]),)

    if all(x in citation for x in CITATION_ENTRIES[3:4]):
        return tuple(citation[x] for x in CITATION_ENTRIES[:4])

    return tuple(citation[x] for x in CITATION_ENTRIES[:3])


def flatten_citation(citation):
    """Flattens a citation dict, from the ``d[CITATION]`` entry in an edge data dictionary

    :param dict[str,str] citation: A PyBEL citation data dictionary
    :rtype: str
    """
    return ','.join('"{}"'.format(e) for e in citation_dict_to_tuple(citation))


def ensure_quotes(s):
    """Quote a string that isn't solely alphanumeric

    :type s: str
    :rtype: str
    """
    return '"{}"'.format(s) if not s.isalnum() else s


CREATION_DATE_FMT = '%Y-%m-%dT%H:%M:%S'
PUBLISHED_DATE_FMT = '%Y-%m-%d'
PUBLISHED_DATE_FMT_2 = '%d:%m:%Y %H:%M'
DATE_VERSION_FMT = '%Y%m%d'


def valid_date(s):
    """Checks that a string represents a valid date in ISO 8601 format YYYY-MM-DD
    
    :type s: str
    :rtype: bool
    """
    try:
        datetime.strptime(s, PUBLISHED_DATE_FMT)
        return True
    except ValueError:
        return False


def valid_date_version(s):
    """Checks that the string is a valid date versions string

    :type s: str
    :rtype: bool
    """
    try:
        datetime.strptime(s, DATE_VERSION_FMT)
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


def hash_node(node_tuple):
    """Converts a PyBEL node tuple to a hash

    :param tuple node_tuple: A BEL node
    :return: A hashed version of the node tuple using :func:`hashlib.sha512` hash of the binary pickle dump
    :rtype: str
    """
    return hashlib.sha512(pickle.dumps(node_tuple)).hexdigest()


def _extract_pybel_data(data):
    """Extracts only the PyBEL-specific data from the given edge data dictionary

    :param dict data: An edge data dictionary
    :rtype: dict
    """
    return {
        key: value
        for key, value in data.items()
        if key in PYBEL_EDGE_DATA_KEYS
    }


def _edge_to_tuple(u, v, data):
    """Converts an edge to tuple

    :param tuple u: The source BEL node
    :param tuple v: The target BEL node
    :param dict data: The edge's data dictionary
    :return: A tuple that can be hashed representing this edge. Makes no promises to its structure.
    """
    extracted_data_dict = _extract_pybel_data(data)
    return u, v, json.dumps(extracted_data_dict, ensure_ascii=False, sort_keys=True)


def hash_edge(u, v, data):
    """Converts an edge tuple to a hash
    
    :param tuple u: The source BEL node
    :param tuple v: The target BEL node
    :param dict data: The edge's data dictionary
    :return: A hashed version of the edge tuple using md5 hash of the binary pickle dump of u, v, and the json dump of d
    :rtype: str
    """
    edge_tuple = _edge_to_tuple(u, v, data)
    edge_tuple_bytes = pickle.dumps(edge_tuple)
    return hashlib.sha512(edge_tuple_bytes).hexdigest()


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
        elif not isinstance(v, (int, string_types, dict, Iterable)):
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
        elif isinstance(v, Iterable) and target[k] not in v:
            return False

    return True


def hash_dump(data):
    """Hashes an arbitrary JSON dictionary by dumping it in sorted order, encoding it in UTF-8, then hashing the bytes

    :param data: An arbitrary JSON-serializable object
    :type data: dict or list or tuple
    :rtype: str
    """
    return hashlib.sha512(json.dumps(data, sort_keys=True).encode('utf-8')).hexdigest()


def hash_citation(type, reference):
    """Creates a hash for a type/reference pair of a citation

    :param str type: The corresponding citation type
    :param str reference: The citation reference
    :rtype: str
    """
    return hash_dump((type, reference))


def hash_evidence(text, type, reference):
    """Creates a hash for an evidence and its citation

    :param str text: The evidence text
    :param str type: The corresponding citation type
    :param str reference: The citation reference
    :rtype: str
    """
    return hash_dump((type, reference, text))
