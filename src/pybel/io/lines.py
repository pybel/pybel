import codecs
import logging
import os

import requests
from requests_file import FileAdapter

from ..graph import BELGraph

__all__ = [
    'from_lines',
    'from_path',
    'from_url'
]

log = logging.getLogger(__name__)


def from_lines(lines, **kwargs):
    """Loads a BEL graph from an iterable over the lines of a BEL script. This can be a list of strings, file, or other.
    This function is a *very* thin wrapper around :class:`BELGraph`.

    :param lines: An iterable of strings (the lines in a BEL script)
    :type lines: iter
    :param kwargs: Keyword arguments to pass to :class:`pybel.BELGraph`
    :return: a parsed BEL graph
    :rtype: BELGraph
    """
    return BELGraph(lines=lines, **kwargs)


def from_path(path, encoding='utf-8', **kwargs):
    """Loads a BEL graph from a file resource

    :param path: A file path
    :type path: str
    :param encoding: the encoding to use when reading this file. Is passed to :code:`codecs.open`.
                     See the python `docs <https://docs.python.org/3/library/codecs.html#standard-encodings>`_ for a
                     list of standard encodings. For example, files starting with a UTF-8 BOM should use
                     :code:`utf_8_sig`
    :type encoding: str
    :param kwargs: Keyword arguments to pass to :class`pybel.BELGraph`
    :return: a parsed BEL graph
    :rtype: BELGraph
    """
    log.info('Loading from path: %s', path)
    with codecs.open(os.path.expanduser(path), encoding=encoding) as file:
        return from_lines(file, **kwargs)


def from_url(url, **kwargs):
    """Loads a BEL graph from a URL resource

    :param url: A valid URL pointing to a BEL resource
    :type url: str
    :param kwargs: Keyword arguments to pass to :class:`pybel.BELGraph`
    :return: a parsed BEL graph
    :rtype: BELGraph
    """
    log.info('Loading from url: %s', url)

    session = requests.session()
    session.mount('file://', FileAdapter())

    response = session.get(url)
    response.raise_for_status()

    lines = (line.decode('utf-8') for line in response.iter_lines())

    return from_lines(lines, **kwargs)
