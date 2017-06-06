# -*- coding: utf-8 -*-

"""This module contains IO functions for BEL scripts"""

import codecs
import logging
import os

from .line_utils import parse_lines
from ..struct import BELGraph
from ..utils import download

__all__ = [
    'from_lines',
    'from_path',
    'from_url'
]

log = logging.getLogger(__name__)


def from_lines(lines, manager=None, allow_naked_names=False, allow_nested=False, allow_unqualified_translocations=False,
               citation_clearing=True, warn_on_singleton=True, **kwargs):
    """Loads a BEL graph from an iterable over the lines of a BEL script

    :param iter[str] lines: An iterable of strings (the lines in a BEL script)
    :param manager: database connection string to cache, pre-built CacheManager, pre-built MetadataParser
                        or None to use default cache
    :type manager: str or :class:`pybel.manager.CacheManager` or :class:`pybel.parser.MetadataParser`
    :param bool allow_naked_names: if true, turn off naked namespace failures
    :param bool allow_nested: if true, turn off nested statement failures
    :param bool allow_unqualified_translocations: If true, allow translocations without TO and FROM clauses.
    :param bool citation_clearing: Should :code:`SET Citation` statements clear evidence and all annotations?
                                Delegated to :class:`pybel.parser.ControlParser`
    :param bool warn_on_singleton: Should the parser thorugh warnings on singletons? Only disable this if you're
                                        sure your BEL Script is syntactically and semantically valid.
    :param dict kwargs: keyword arguments to pass to :class:`networkx.MultiDiGraph`
    :return: A BEL graph
    :rtype: BELGraph
    """
    graph = BELGraph(**kwargs)
    parse_lines(
        graph=graph,
        lines=lines,
        manager=manager,
        allow_naked_names=allow_naked_names,
        allow_nested=allow_nested,
        allow_unqualified_translocations=allow_unqualified_translocations,
        citation_clearing=citation_clearing,
        warn_on_singleton=warn_on_singleton,
    )
    return graph


def from_path(path, manager=None, allow_naked_names=False, allow_nested=False, citation_clearing=True,
              warn_on_singleton=True, encoding='utf-8', **kwargs):
    """Loads a BEL graph from a file resource. This function is a thin wrapper around :func:`from_lines`.

    :param str path: A file path
    :param manager: database connection string to cache, pre-built CacheManager, pre-built MetadataParser
                        or None to use default cache
    :type manager: str or :class:`pybel.manager.CacheManager` or :class:`pybel.parser.MetadataParser`
    :param bool allow_naked_names: if true, turn off naked namespace failures
    :param bool allow_nested: if true, turn off nested statement failures
    :param bool citation_clearing: Should :code:`SET Citation` statements clear evidence and all annotations?
                                Delegated to :class:`pybel.parser.ControlParser`
    :param bool warn_on_singleton: Should the parser thorugh warnings on singletons? Only disable this if you're
                                        sure your BEL Script is syntactically and semantically valid.
    :param str encoding: the encoding to use when reading this file. Is passed to :code:`codecs.open`.
                     See the python `docs <https://docs.python.org/3/library/codecs.html#standard-encodings>`_ for a
                     list of standard encodings. For example, files starting with a UTF-8 BOM should use
                     :code:`utf_8_sig`
    :param dict kwargs: Keyword arguments to pass to :class:`networkx.MultiDiGraph`
    :return: A BEL graph
    :rtype: BELGraph
    """
    log.info('Loading from path: %s', path)
    with codecs.open(os.path.expanduser(path), encoding=encoding) as file:
        return from_lines(
            lines=file,
            manager=manager,
            allow_naked_names=allow_naked_names,
            allow_nested=allow_nested,
            citation_clearing=citation_clearing,
            warn_on_singleton=warn_on_singleton,
            **kwargs
        )


def from_url(url, manager=None, allow_naked_names=False, allow_nested=False, citation_clearing=True,
             warn_on_singleton=True, **kwargs):
    """Loads a BEL graph from a URL resource. This function is a thin wrapper around :func:`from_lines`.

    :param str url: A valid URL pointing to a BEL resource
    :param manager: database connection string to cache, pre-built CacheManager, pre-built MetadataParser
                        or None to use default cache
    :type manager: str or :class:`pybel.manager.CacheManager` or :class:`pybel.parser.MetadataParser`
    :param bool allow_naked_names: if true, turn off naked namespace failures
    :param bool allow_nested: if true, turn off nested statement failures
    :param bool citation_clearing: Should :code:`SET Citation` statements clear evidence and all annotations?
                                Delegated to :class:`pybel.parser.ControlParser`
    :param bool warn_on_singleton: Should the parser thorugh warnings on singletons? Only disable this if you're
                                        sure your BEL Script is syntactically and semantically valid.
    :param dict kwargs: Keyword arguments to pass to :class:`networkx.MultiDiGraph`
    :return: A BEL graph
    :rtype: BELGraph
    """
    log.info('Loading from url: %s', url)

    res = download(url)
    lines = (line.decode('utf-8') for line in res.iter_lines())

    return from_lines(
        lines=lines,
        manager=manager,
        allow_naked_names=allow_naked_names,
        allow_nested=allow_nested,
        citation_clearing=citation_clearing,
        warn_on_singleton=warn_on_singleton,
        **kwargs
    )
