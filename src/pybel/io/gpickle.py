# -*- coding: utf-8 -*-

"""Conversion functions for BEL graphs with bytes and Python pickles."""

import gzip
from io import BytesIO
from typing import BinaryIO, Union

from networkx.utils import open_file

from .utils import raise_for_not_bel, raise_for_old_graph
from ..struct.graph import BELGraph

try:
    import pickle5 as pickle
except ImportError:
    import pickle

__all__ = [
    'to_bytes',
    'from_bytes',
    'to_bytes_gz',
    'from_bytes_gz',
    'to_pickle',
    'to_pickle_gz',
    'from_pickle',
    'from_pickle_gz',
]


def to_bytes(graph: BELGraph, protocol: int = pickle.HIGHEST_PROTOCOL) -> bytes:
    """Convert a graph to bytes with pickle.

    Note that the pickle module has some incompatibilities between Python 2 and 3. To export a universally importable
    pickle, choose 0, 1, or 2.

    :param graph: A BEL graph
    :param protocol: Pickling protocol to use. Defaults to ``HIGHEST_PROTOCOL``.

    .. seealso:: https://docs.python.org/3.6/library/pickle.html#data-stream-format
    """
    raise_for_not_bel(graph)
    return pickle.dumps(graph, protocol=protocol)


def from_bytes(bytes_graph: bytes, check_version: bool = True) -> BELGraph:
    """Read a graph from bytes (the result of pickling the graph).

    :param bytes_graph: File or filename to write
    :param check_version: Checks if the graph was produced by this version of PyBEL
    """
    graph = pickle.loads(bytes_graph)

    raise_for_not_bel(graph)
    if check_version:
        raise_for_old_graph(graph)

    return graph


def to_bytes_gz(graph: BELGraph, protocol: int = pickle.HIGHEST_PROTOCOL) -> bytes:
    """Convert a graph to gzipped bytes with pickle.

    :param graph: A BEL graph
    :param protocol: Pickling protocol to use. Defaults to ``HIGHEST_PROTOCOL``.
    """
    io = BytesIO()
    with gzip.open(io, mode='wb') as file:
        pickle.dump(graph, file, protocol=protocol)
    return io.getvalue()


def from_bytes_gz(bytes_graph: bytes) -> BELGraph:
    """Read a graph from gzipped bytes (the result of pickling the graph).

    :param bytes_graph: File or filename to write
    """
    with gzip.GzipFile(fileobj=BytesIO(bytes_graph), mode='rb') as file:
        return pickle.load(file)


@open_file(1, mode='wb')
def to_pickle(graph: BELGraph, path: Union[str, BinaryIO], protocol: int = pickle.HIGHEST_PROTOCOL) -> None:
    """Write this graph to a pickle file.

    Note that the pickle module has some incompatibilities between Python 2 and 3. To export a universally importable
    pickle, choose 0, 1, or 2.

    :param graph: A BEL graph
    :param path: A path or file-like
    :param protocol: Pickling protocol to use. Defaults to ``HIGHEST_PROTOCOL``.

    .. seealso:: https://docs.python.org/3.6/library/pickle.html#data-stream-format
    """
    raise_for_not_bel(graph)
    pickle.dump(graph, path, protocol)


def to_pickle_gz(graph: BELGraph, path: str, protocol: int = pickle.HIGHEST_PROTOCOL) -> None:
    """Write this graph to a gzipped pickle file."""
    with gzip.open(path, 'wb') as file:
        to_pickle(graph, file, protocol=protocol)


@open_file(0, mode='rb')
def from_pickle(path: Union[str, BinaryIO], check_version: bool = True) -> BELGraph:
    """Read a graph from a pickle file.

    :param path: File or filename to read. Filenames ending in .gz or .bz2 will be uncompressed.
    :param bool check_version: Checks if the graph was produced by this version of PyBEL
    """
    graph = pickle.load(path)

    raise_for_not_bel(graph)
    if check_version:
        raise_for_old_graph(graph)

    return graph


def from_pickle_gz(path: str) -> BELGraph:
    """Read a graph from a gzipped pickle file."""
    with gzip.open(path, 'rb') as file:
        return from_pickle(file)
