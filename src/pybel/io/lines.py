# -*- coding: utf-8 -*-

"""This module contains IO functions for BEL scripts."""

import codecs
import logging
import os

from .line_utils import parse_lines
from ..resources.utils import download
from ..struct import BELGraph

__all__ = [
    'from_lines',
    'from_path',
    'from_url'
]

log = logging.getLogger(__name__)


def from_lines(lines, manager=None, allow_nested=False, citation_clearing=True, use_tqdm=False, **kwargs):
    """Load a BEL graph from an iterable over the lines of a BEL script.

    :param iter[str] lines: An iterable of strings (the lines in a BEL script)
    :type manager: Optional[pybel.manager.Manager]
    :param bool allow_nested: if true, turn off nested statement failures
    :param bool citation_clearing: Should :code:`SET Citation` statements clear evidence and all annotations?
                                Delegated to :class:`pybel.parser.ControlParser`
    :param bool use_tqdm: If true, use tqdm for logging
    :param dict kwargs: keyword arguments to :func:`pybel.io.line_utils.parse_lines`
    :rtype: BELGraph
    """
    graph = BELGraph()
    parse_lines(
        graph=graph,
        lines=lines,
        manager=manager,
        allow_nested=allow_nested,
        citation_clearing=citation_clearing,
        use_tqdm=use_tqdm,
        **kwargs
    )
    return graph


def from_path(path, manager=None, allow_nested=False, citation_clearing=True, encoding='utf-8', use_tqdm=False,
              **kwargs):
    """Load a BEL graph from a file resource. This function is a thin wrapper around :func:`from_lines`.

    :param str path: A file path
    :type manager: Optional[pybel.manager.Manager]
    :param bool allow_nested: if true, turn off nested statement failures
    :param bool citation_clearing: Should :code:`SET Citation` statements clear evidence and all annotations?
                                Delegated to :class:`pybel.parser.ControlParser`
    :param str encoding: the encoding to use when reading this file. Is passed to :code:`codecs.open`.
                     See the python `docs <https://docs.python.org/3/library/codecs.html#standard-encodings>`_ for a
                     list of standard encodings. For example, files starting with a UTF-8 BOM should use
                     :code:`utf_8_sig`
    :param bool use_tqdm: If true, use tqdm for logging
    :param dict kwargs: keyword arguments to :func:`pybel.io.line_utils.parse_lines`
    :rtype: BELGraph
    """
    log.info('Loading from path: %s', path)
    with codecs.open(os.path.expanduser(path), encoding=encoding) as file:
        return from_lines(
            lines=file,
            manager=manager,
            allow_nested=allow_nested,
            citation_clearing=citation_clearing,
            use_tqdm=use_tqdm,
            **kwargs
        )


def from_url(url, manager=None, allow_nested=False, citation_clearing=True, use_tqdm=False, **kwargs):
    """Load a BEL graph from a URL resource. This function is a thin wrapper around :func:`from_lines`.

    :param str url: A valid URL pointing to a BEL resource
    :param manager: database connection string to cache, pre-built :class:`Manager`, or None to use default cache
    :type manager: None or str or pybel.manager.Manager
    :param bool allow_nested: if true, turn off nested statement failures
    :param bool citation_clearing: Should :code:`SET Citation` statements clear evidence and all annotations?
                                Delegated to :class:`pybel.parser.ControlParser`
    :param bool use_tqdm: If true, use tqdm for logging
    :param dict kwargs: keyword arguments to :func:`pybel.io.line_utils.parse_lines`
    :rtype: BELGraph
    """
    log.info('Loading from url: %s', url)

    res = download(url)
    lines = (line.decode('utf-8') for line in res.iter_lines())

    return from_lines(
        lines=lines,
        manager=manager,
        allow_nested=allow_nested,
        citation_clearing=citation_clearing,
        use_tqdm=use_tqdm,
        **kwargs
    )
