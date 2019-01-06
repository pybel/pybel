# -*- coding: utf-8 -*-

"""This module contains IO functions for BEL scripts."""

import codecs
import logging
import os
from typing import Iterable

from bel_resources.utils import download
from .line_utils import parse_lines
from ..struct import BELGraph

__all__ = [
    'from_lines',
    'from_path',
    'from_url'
]

log = logging.getLogger(__name__)


def from_lines(lines: Iterable[str], **kwargs) -> BELGraph:
    """Load a BEL graph from an iterable over the lines of a BEL script.

    :param lines: An iterable of strings (the lines in a BEL script)

    The remaining keyword arguments are passed to :func:`pybel.io.line_utils.parse_lines`.
    """
    graph = BELGraph()
    parse_lines(graph=graph, lines=lines, **kwargs)
    return graph


def from_path(path: str, encoding: str = 'utf-8', **kwargs) -> BELGraph:
    """Load a BEL graph from a file resource. This function is a thin wrapper around :func:`from_lines`.

    :param path: A file path
    :param encoding: the encoding to use when reading this file. Is passed to :code:`codecs.open`. See the python
     `docs <https://docs.python.org/3/library/codecs.html#standard-encodings>`_ for a list of standard encodings. For
     example, files starting with a UTF-8 BOM should use :code:`utf_8_sig`.

    The remaining keyword arguments are passed to :func:`pybel.io.line_utils.parse_lines`.
    """
    log.info('Loading from path: %s', path)
    graph = BELGraph(path=path)
    with codecs.open(os.path.expanduser(path), encoding=encoding) as lines:
        parse_lines(graph=graph, lines=lines, **kwargs)
    return graph


def from_url(url: str, **kwargs) -> BELGraph:
    """Load a BEL graph from a URL resource.

    :param url: A valid URL pointing to a BEL document

    The remaining keyword arguments are passed to :func:`pybel.io.line_utils.parse_lines`.
    """
    log.info('Loading from url: %s', url)
    res = download(url)
    lines = (line.decode('utf-8') for line in res.iter_lines())

    graph = BELGraph(path=url)
    parse_lines(graph=graph, lines=lines, **kwargs)
    return graph
