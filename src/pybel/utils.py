# -*- coding: utf-8 -*-

import logging
from collections import defaultdict, MutableMapping
from configparser import ConfigParser

import networkx as nx
import requests
from requests_file import FileAdapter

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
