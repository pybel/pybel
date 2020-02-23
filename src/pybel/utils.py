# -*- coding: utf-8 -*-

"""Utilities for PyBEL."""

import hashlib
import json
import logging
import pickle
from collections import defaultdict
from collections.abc import Iterable, MutableMapping
from datetime import datetime
from typing import Any, Mapping, Optional, Tuple

from .constants import (
    ACTIVITY, CITATION, CITATION_DB, CITATION_DB_NAME, CITATION_IDENTIFIER, DEGRADATION, EFFECT, EVIDENCE, FROM_LOC,
    IDENTIFIER, LOCATION, MODIFIER, NAME, NAMESPACE, OBJECT, RELATION, SUBJECT, TO_LOC, TRANSLOCATION,
)
from .typing import EdgeData

logger = logging.getLogger(__name__)

CanonicalEdge = Tuple[str, Optional[Tuple], Optional[Tuple]]


def expand_dict(flat_dict, sep: str = '_'):
    """Expand a flattened dictionary.

    :param dict flat_dict: a nested dictionary that has been flattened so the keys are composite
    :param sep: the separator between concatenated keys
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


def flatten_dict(
    data: Mapping[str, Any],
    parent_key: str = '',
    sep: str = '_',
) -> Mapping[str, str]:
    """Flatten a nested dictionary.

    :param data: A nested dictionary
    :param parent_key: The parent's key. This is a value for tail recursion, so don't set it yourself.
    :param sep: The separator used between dictionary levels
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


def tokenize_version(version_string: str) -> Tuple[int, int, int]:
    """Tokenize a version string to a tuple.

    Truncates qualifiers like ``-dev``.

    :param version_string: A version string
    :return: A tuple representing the version string

    >>> tokenize_version('0.1.2-dev')
    (0, 1, 2)
    """
    before_dash = version_string.split('-')[0]
    major, minor, patch = before_dash.split('.')[:3]  # take only the first 3 in case there's an extension like -dev.0
    return int(major), int(minor), int(patch)


def ensure_quotes(s: str) -> str:
    """Quote a string that isn't solely alphanumeric."""
    return '"{}"'.format(s) if not s.isalnum() else s


CREATION_DATE_FMT = '%Y-%m-%dT%H:%M:%S'
PUBLISHED_DATE_FMT = '%Y-%m-%d'
PUBLISHED_DATE_FMT_2 = '%d:%m:%Y %H:%M'
DATE_VERSION_FMT = '%Y%m%d'


def valid_date(s: str) -> bool:
    """Check that a string represents a valid date in ISO 8601 format YYYY-MM-DD."""
    return _validate_date_fmt(s, PUBLISHED_DATE_FMT)


def valid_date_version(s: str) -> bool:
    """Check that the string is a valid date versions string."""
    return _validate_date_fmt(s, DATE_VERSION_FMT)


def _validate_date_fmt(s: str, fmt: str) -> bool:
    try:
        datetime.strptime(s, fmt)
    except ValueError:
        return False
    else:
        return True


def parse_datetime(s: str) -> datetime.date:
    """Try to parse a datetime object from a standard datetime format or date format."""
    for fmt in (CREATION_DATE_FMT, PUBLISHED_DATE_FMT, PUBLISHED_DATE_FMT_2):
        try:
            dt = datetime.strptime(s, fmt)
        except ValueError:
            pass
        else:
            return dt

    raise ValueError('Incorrect datetime format for {}'.format(s))


def _get_citation_str(data: Mapping) -> Optional[str]:
    citation = data.get(CITATION)
    if citation is not None:
        return '{}:{}'.format(citation[CITATION_DB], citation[CITATION_IDENTIFIER])


def hash_edge(source, target, edge_data: EdgeData) -> str:
    """Convert an edge tuple to a MD5 hash.

    :param BaseEntity source: The source BEL node
    :param BaseEntity target: The target BEL node
    :param edge_data: The edge's data dictionary
    :return: A hashed version of the edge tuple using MD5 hash of the binary pickle dump of u, v, and the json dump
     of d
    """
    edge_tuple = _get_edge_tuple(source, target, edge_data)
    edge_tuple_bytes = pickle.dumps(edge_tuple)
    return hashlib.md5(edge_tuple_bytes).hexdigest()  # noqa: S303


def _get_edge_tuple(
    source,
    target,
    edge_data: EdgeData,
) -> Tuple[str, str, Optional[str], Optional[str], CanonicalEdge]:
    """Convert an edge to a consistent tuple.

    :param BaseEntity source: The source BEL node
    :param BaseEntity target: The target BEL node
    :param edge_data: The edge's data dictionary
    :return: A tuple that can be hashed representing this edge. Makes no promises to its structure.
    """
    return (
        source.as_bel(),
        target.as_bel(),
        _get_citation_str(edge_data),
        edge_data.get(EVIDENCE),
        canonicalize_edge(edge_data),
    )


def subdict_matches(target: Mapping, query: Mapping, partial_match: bool = True) -> bool:
    """Check if all the keys in the query dict are in the target dict, and that their values match.

    1. Checks that all keys in the query dict are in the target dict
    2. Matches the values of the keys in the query dict
        a. If the value is a string, then must match exactly
        b. If the value is a set/list/tuple, then will match any of them
        c. If the value is a dict, then recursively check if that subdict matches

    :param target: The dictionary to search
    :param query: A query dict with keys to match
    :param partial_match: Should the query values be used as partial or exact matches? Defaults to :code:`True`.
    :return: if all keys in b are in target_dict and their values match
    """
    for k, v in query.items():
        if k not in target:
            return False
        elif not isinstance(v, (int, str, dict, Iterable)):
            raise ValueError('invalid value: {}'.format(v))
        elif isinstance(v, (int, str)) and target[k] != v:
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


def hash_dump(data) -> str:
    """Hash an arbitrary JSON dictionary by dumping it in sorted order, encoding it in UTF-8, then hashing the bytes.

    :param data: An arbitrary JSON-serializable object
    :type data: dict or list or tuple
    """
    return hashlib.md5(json.dumps(data, sort_keys=True).encode('utf-8')).hexdigest()  # noqa: S303


def canonicalize_edge(edge_data: EdgeData) -> CanonicalEdge:
    """Canonicalize the edge to a tuple based on the relation, subject modifications, and object modifications."""
    return (
        edge_data[RELATION],
        _canonicalize_edge_modifications(edge_data.get(SUBJECT)),
        _canonicalize_edge_modifications(edge_data.get(OBJECT)),
    )


def _canonicalize_edge_modifications(edge_data: EdgeData) -> Optional[Tuple]:
    """Return the SUBJECT or OBJECT entry of a PyBEL edge data dictionary as a canonical tuple."""
    if edge_data is None:
        return

    modifier = edge_data.get(MODIFIER)
    location = edge_data.get(LOCATION)
    effect = edge_data.get(EFFECT)

    if modifier is None and location is None:
        return

    result = []

    if modifier == ACTIVITY:
        if effect:
            t = (
                ACTIVITY,
                effect[NAMESPACE],
                effect.get(IDENTIFIER),
                effect.get(NAME),
            )
        else:
            t = (ACTIVITY,)
        result.append(t)

    elif modifier == DEGRADATION:
        t = (DEGRADATION,)
        result.append(t)

    elif modifier == TRANSLOCATION:
        if effect:
            from_loc_concept = effect[FROM_LOC]
            to_loc_concept = effect[TO_LOC]

            t = (
                TRANSLOCATION,
                from_loc_concept[NAMESPACE],
                from_loc_concept.get(IDENTIFIER),
                from_loc_concept.get(NAME),
                to_loc_concept[NAMESPACE],
                to_loc_concept.get(IDENTIFIER),
                to_loc_concept.get(NAME),
            )
        else:
            t = (TRANSLOCATION,)
        result.append(t)

    if location:
        t = (
            LOCATION,
            location[NAMESPACE],
            location.get(IDENTIFIER),
            location.get(NAME),
        )
        result.append(t)

    if not result:
        raise ValueError('Invalid data: {}'.format(edge_data))

    return tuple(result)


def get_corresponding_pickle_path(path: str) -> str:
    """Get the same path with a pickle extension.

    :param path: A path to a BEL file.
    """
    return '{path}.pickle'.format(path=path)


def citation_dict(*, db: str, db_id: str, db_name: Optional[str] = None, **kwargs):
    """Make a citation dictionary."""
    return CitationDict(db=db, db_id=db_id, db_name=db_name, **kwargs)


class CitationDict(dict):
    """A dictionary describing a citation."""

    def __init__(self, db: str, db_id: str, *, db_name: Optional[str] = None, **kwargs):
        super().__init__()
        self[CITATION_DB] = db
        self[CITATION_IDENTIFIER] = db_id
        if db_name is not None:
            self[CITATION_DB_NAME] = db_name
        self.update(kwargs)

    def __hash__(self):
        return hash((self[CITATION_DB], self[CITATION_IDENTIFIER]))
