# -*- coding: utf-8 -*-

"""This module contains IO functions for BEL scripts."""

import gzip
import logging
from typing import TextIO, Union

from networkx.utils import open_file

from bel_resources.utils import download
from .line_utils import parse_lines
from ..struct import BELGraph

__all__ = [
    'from_bel_script',
    'from_bel_script_gz',
    'from_bel_script_url',
]

logger = logging.getLogger(__name__)


@open_file(0, mode='r')
def from_bel_script(path: Union[str, TextIO], **kwargs) -> BELGraph:
    """Load a BEL graph from a file resource. This function is a thin wrapper around :func:`from_lines`.

    :param path: A path or file-like

    The remaining keyword arguments are passed to :func:`pybel.io.line_utils.parse_lines`,
    which populates a :class:`BELGraph`.
    """
    logger.info('Reading BEL script at %s', path.name)
    graph = BELGraph(path=path.name)
    parse_lines(graph=graph, lines=path, **kwargs)
    return graph


def from_bel_script_gz(path, **kwargs) -> BELGraph:
    """Parse a BEL graph from a gzipped BEL Script."""
    with gzip.open(path, 'rt') as file:
        return from_bel_script(file, **kwargs)


def from_bel_script_url(url: str, **kwargs) -> BELGraph:
    """Load a BEL graph from a URL resource.

    :param url: A valid URL pointing to a BEL document

    The remaining keyword arguments are passed to :func:`pybel.io.line_utils.parse_lines`.
    """
    logger.info('Loading from url: %s', url)
    res = download(url)
    lines = (line.decode('utf-8') for line in res.iter_lines())

    graph = BELGraph(path=url)
    parse_lines(graph=graph, lines=lines, **kwargs)
    return graph
