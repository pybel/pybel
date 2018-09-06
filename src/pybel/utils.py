# -*- coding: utf-8 -*-

"""Utilities for PyBEL."""

import hashlib
import json
import logging
from collections import Iterable, MutableMapping, defaultdict
from datetime import datetime

from six import string_types
from six.moves.cPickle import dumps

from .constants import (
    ACTIVITY, CITATION, CITATION_REFERENCE, CITATION_TYPE, DEGRADATION, EFFECT, EVIDENCE, FROM_LOC, IDENTIFIER,
    LOCATION, MODIFIER, NAME, NAMESPACE, OBJECT, RELATION, SUBJECT, TO_LOC, TRANSLOCATION, VERSION,
)

log = logging.getLogger(__name__)


def expand_dict(flat_dict, sep='_'):
    """Expand a flattened dictionary.

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


def flatten_dict(data, parent_key='', sep='_'):
    """Flatten a nested dictionary.

    :param data: A nested dictionary
    :type data: dict or MutableMapping
    :param str parent_key: The parent's key. This is a value for tail recursion, so don't set it yourself.
    :param str sep: The separator used between dictionary levels
    :rtype: dict

    .. seealso:: http://stackoverflow.com/a/6027615
    """
    items = {}

    for key, value in data.items():
        # prepend the parent key
        key = parent_key + sep + key if parent_key else key

        if isinstance(value, (dict, MutableMapping)):
            items.update(flatten_dict(value, key, sep=sep))
        elif isinstance(value, (set, list)):
            items[key] = ','.join(value)
        else:
            items[key] = value

    return items


def get_version():
    """Get the current PyBEL version.

    :return: The current PyBEL version
    :rtype: str
    """
    return VERSION


def tokenize_version(version_string):
    """Tokenize a version string to a tuple.

    Truncates qualifiers like ``-dev``.

    :param str version_string: A version string
    :return: A tuple representing the version string
    :rtype: tuple

    >>> tokenize_version('0.1.2-dev')
    (0, 1, 2)

    """
    before_dash = version_string.split('-')[0]
    version_tuple = before_dash.split('.')[:3]  # take only the first 3 in case there's an extension like -dev.0
    return tuple(map(int, version_tuple))


def ensure_quotes(s):
    """Quote a string that isn't solely alphanumeric.

    :type s: str
    :rtype: str
    """
    return '"{}"'.format(s) if not s.isalnum() else s


CREATION_DATE_FMT = '%Y-%m-%dT%H:%M:%S'
PUBLISHED_DATE_FMT = '%Y-%m-%d'
PUBLISHED_DATE_FMT_2 = '%d:%m:%Y %H:%M'
DATE_VERSION_FMT = '%Y%m%d'


def valid_date(s):
    """Check that a string represents a valid date in ISO 8601 format YYYY-MM-DD.
    
    :type s: str
    :rtype: bool
    """
    try:
        datetime.strptime(s, PUBLISHED_DATE_FMT)
        return True
    except ValueError:
        return False


def valid_date_version(s):
    """Check that the string is a valid date versions string.

    :type s: str
    :rtype: bool
    """
    try:
        datetime.strptime(s, DATE_VERSION_FMT)
        return True
    except ValueError:
        return False


def parse_datetime(s):
    """Try to parse a datetime object from a standard datetime format or date format.

    :param str s: A string representing a date or datetime
    :return: A parsed date object
    :rtype: datetime.date
    """
    for fmt in (CREATION_DATE_FMT, PUBLISHED_DATE_FMT, PUBLISHED_DATE_FMT_2):
        try:
            dt = datetime.strptime(s, fmt)
        except ValueError:
            pass
        else:
            return dt

    raise ValueError('Incorrect datetime format for {}'.format(s))


def _hash_tuple(t):
    return hashlib.sha512(dumps(t)).hexdigest()


def _get_citation_tuple(data):
    citation = data.get(CITATION)

    if citation is None:
        return None, None

    return '{type}:{reference}'.format(type=citation[CITATION_TYPE], reference=citation[CITATION_REFERENCE])


def _get_edge_tuple(u, v, data):
    """Convert an edge to a consistent tuple.

    :param BaseEntity u: The source BEL node
    :param BaseEntity v: The target BEL node
    :param dict data: The edge's data dictionary
    :return: A tuple that can be hashed representing this edge. Makes no promises to its structure.
    """
    return (
        u.as_bel(),
        v.as_bel(),
        _get_citation_tuple(data),
        data.get(EVIDENCE),
        canonicalize_edge(data),
    )


def hash_edge(u, v, data):
    """Convert an edge tuple to a SHA512 hash.

    :param BaseEntity u: The source BEL node
    :param BaseEntity v: The target BEL node
    :param dict data: The edge's data dictionary
    :return: A hashed version of the edge tuple using md5 hash of the binary pickle dump of u, v, and the json dump of d
    :rtype: str
    """
    edge_tuple = _get_edge_tuple(u, v, data)
    return _hash_tuple(edge_tuple)


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
    """Hash an arbitrary JSON dictionary by dumping it in sorted order, encoding it in UTF-8, then hashing the bytes.

    :param data: An arbitrary JSON-serializable object
    :type data: dict or list or tuple
    :rtype: str
    """
    return hashlib.sha512(json.dumps(data, sort_keys=True).encode('utf-8')).hexdigest()


def hash_citation(type, reference):
    """Create a hash for a type/reference pair of a citation.

    :param str type: The corresponding citation type
    :param str reference: The citation reference
    :rtype: str
    """
    s = u'{type}:{reference}'.format(type=type, reference=reference)
    return hashlib.sha512(s.encode('utf8')).hexdigest()


def hash_evidence(text, type, reference):
    """Create a hash for an evidence and its citation.

    :param str text: The evidence text
    :param str type: The corresponding citation type
    :param str reference: The citation reference
    :rtype: str
    """
    s = u'{type}:{reference}:{text}'.format(type=type, reference=reference, text=text)
    return hashlib.sha512(s.encode('utf8')).hexdigest()


def canonicalize_edge(data):
    """Canonicalize the edge to a tuple based on the relation, subject modifications, and object modifications.

    :param dict data: A PyBEL edge data dictionary
    :return: A 3-tuple that's specific for the edge (relation, subject, object)
    :rtype: tuple
    """
    return (
        data[RELATION],
        _canonicalize_edge_modifications(data.get(SUBJECT)),
        _canonicalize_edge_modifications(data.get(OBJECT)),
    )


def _canonicalize_edge_modifications(data):
    """Return the SUBJECT or OBJECT entry of a PyBEL edge data dictionary as a canonical tuple.

    :param dict data: A PyBEL edge data dictionary
    :rtype: tuple
    """
    if data is None:
        return

    modifier = data.get(MODIFIER)
    location = data.get(LOCATION)
    effect = data.get(EFFECT)

    if modifier is None and location is None:
        return

    result = []

    if modifier == ACTIVITY:
        if effect:
            effect_name = effect.get(NAME)
            effect_identifier = effect.get(IDENTIFIER)

            t = (
                ACTIVITY,
                effect[NAMESPACE],
                effect_name or effect_identifier,
            )

        else:
            t = (ACTIVITY,)

        result.append(t)

    elif modifier == DEGRADATION:
        t = (DEGRADATION,)
        result.append(t)

    elif modifier == TRANSLOCATION:
        if effect:
            from_loc_name = effect[FROM_LOC].get(NAME)
            from_loc_identifier = effect[FROM_LOC].get(IDENTIFIER)
            to_loc_name = effect[TO_LOC].get(NAME)
            to_loc_identifier = effect[TO_LOC].get(IDENTIFIER)

            t = (
                TRANSLOCATION,
                data[EFFECT][FROM_LOC][NAMESPACE],
                from_loc_name or from_loc_identifier,
                data[EFFECT][TO_LOC][NAMESPACE],
                to_loc_name or to_loc_identifier,
            )
        else:
            t = (TRANSLOCATION,)
        result.append(t)

    if location:
        location_name = location.get(NAME)
        location_identifier = location.get(IDENTIFIER)

        t = (
            LOCATION,
            location[NAMESPACE],
            location_name or location_identifier,
        )
        result.append(t)

    if not result:
        raise ValueError('Invalid data: {}'.format(data))

    return tuple(result)


def get_corresponding_pickle_path(path):
    """Get the same path with a pickle extension.

    :param str path: A path to a BEL file.
    :rtype: str
    """
    return '{path}.pickle'.format(path=path)
