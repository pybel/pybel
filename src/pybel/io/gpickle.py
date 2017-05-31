# -*- coding: utf-8 -*-

"""

Bytes
-----
This module contains IO functions for interconversion between BEL graphs and python pickle objects

"""

from networkx import read_gpickle, write_gpickle

from .utils import raise_for_not_bel, raise_for_old_graph
from ..graph import BELGraph

try:
    import cPickle as pickle
except ImportError:
    import pickle

__all__ = [
    'to_bytes',
    'from_bytes',
    'to_pickle',
    'from_pickle',
]


def to_bytes(graph, protocol=None):
    """Converts a graph to bytes with pickle.

    :param graph: A BEL graph
    :type graph: BELGraph
    :param protocol: Pickling protocol to use
    :type protocol: int
    :return: Pickled bytes representing the graph
    :rtype: bytes
    """
    raise_for_not_bel(graph)

    if protocol is not None:
        return pickle.dumps(graph, protocol=protocol)
    else:
        return pickle.dumps(graph)


def from_bytes(bytes_graph, check_version=True):
    """Reads a graph from bytes (the result of pickling the graph).

    :param bytes_graph: File or filename to write
    :type bytes_graph: bytes
    :param check_version: Checks if the graph was produced by this version of PyBEL
    :type check_version: bool
    :return: A BEL graph
    :rtype: BELGraph
    """
    graph = pickle.loads(bytes_graph)

    raise_for_not_bel(graph)
    if check_version:
        raise_for_old_graph(graph)

    return graph


def to_pickle(graph, file, protocol=None):
    """Writes this graph to a pickle object with :func:`networkx.write_gpickle`.

    :param graph: A BEL graph
    :type graph: BELGraph
    :param file: A file or filename to write to
    :type file: file or file-like or str
    :param protocol: Pickling protocol to use
    :type protocol: int
    """
    raise_for_not_bel(graph)

    if protocol is not None:
        write_gpickle(graph, file, protocol=protocol)
    else:
        write_gpickle(graph, file)


def from_pickle(path, check_version=True):
    """Reads a graph from a gpickle file.

    :param path: File or filename to read. Filenames ending in .gz or .bz2 will be uncompressed.
    :type path: file or str
    :param check_version: Checks if the graph was produced by this version of PyBEL
    :type check_version: bool
    :return: A BEL graph
    :rtype: BELGraph
    """
    graph = read_gpickle(path)

    raise_for_not_bel(graph)
    if check_version:
        raise_for_old_graph(graph)

    return graph
