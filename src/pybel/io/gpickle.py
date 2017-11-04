# -*- coding: utf-8 -*-

"""

Bytes
-----
This module contains IO functions for interconversion between BEL graphs and python pickle objects

"""

from networkx import read_gpickle, write_gpickle
from six.moves.cPickle import HIGHEST_PROTOCOL, dumps, loads

from .utils import raise_for_not_bel, raise_for_old_graph
from ..struct import BELGraph

__all__ = [
    'to_bytes',
    'from_bytes',
    'to_pickle',
    'from_pickle',
]


def to_bytes(graph, protocol=HIGHEST_PROTOCOL):
    """Converts a graph to bytes with pickle. Note that the pickle module has some incompatibilities between Python
    2 and 3. To export a universally importable pickle, choose 0, 1, or 2.

    :param BELGraph graph: A BEL network
    :param int protocol: Pickling protocol to use
    :return: Pickled bytes representing the graph
    :rtype: bytes

    .. seealso:: https://docs.python.org/3.6/library/pickle.html#data-stream-format
    """
    raise_for_not_bel(graph)
    return dumps(graph, protocol=protocol)


def from_bytes(bytes_graph, check_version=True):
    """Reads a graph from bytes (the result of pickling the graph).

    :param bytes bytes_graph: File or filename to write
    :param bool check_version: Checks if the graph was produced by this version of PyBEL
    :return: A BEL graph
    :rtype: BELGraph
    """
    graph = loads(bytes_graph)

    raise_for_not_bel(graph)
    if check_version:
        raise_for_old_graph(graph)

    return graph


def to_pickle(graph, file, protocol=HIGHEST_PROTOCOL):
    """Writes this graph to a pickle object with :func:`networkx.write_gpickle`.  Note that the pickle module has some
    incompatibilities between Python 2 and 3. To export a universally importable pickle, choose 0, 1, or 2.

    :param BELGraph graph: A BEL graph
    :param str or file: A file or filename to write to
    :param int protocol: Pickling protocol to use

    .. seealso:: https://docs.python.org/3.6/library/pickle.html#data-stream-format
    """
    raise_for_not_bel(graph)
    write_gpickle(graph, file, protocol=protocol)


def from_pickle(path, check_version=True):
    """Reads a graph from a gpickle file.

    :param file or str path: File or filename to read. Filenames ending in .gz or .bz2 will be uncompressed.
    :param bool check_version: Checks if the graph was produced by this version of PyBEL
    :return: A BEL graph
    :rtype: BELGraph
    """
    graph = read_gpickle(path)

    raise_for_not_bel(graph)
    if check_version:
        raise_for_old_graph(graph)

    return graph
