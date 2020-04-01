# -*- coding: utf-8 -*-

"""Contains the main data structure for PyBEL."""

import os
from typing import TextIO, Union

from networkx.utils import open_file
from pkg_resources import iter_entry_points

from ..struct import BELGraph

__all__ = [
    'load',
    'dump',
    'InvalidExtensionError',
]

#: Mapping from extension to importer function
IMPORTERS = {
    entry.name: entry.load()
    for entry in iter_entry_points(group='pybel.importer')
}

#: Mapping from extension to exporter function
EXPORTERS = {
    entry.name: entry.load()
    for entry in iter_entry_points(group='pybel.exporter')
}


class InvalidExtensionError(ValueError):
    """Raised when an invalid extension is used."""

    def __init__(self, path):
        fname = os.path.basename(path)
        super().__init__('Invalid extension for file: {}'.format(fname))


def load(path: str, **kwargs) -> BELGraph:
    """Read a BEL graph.

    :param path: The path to a BEL graph in any of the formats
     with extensions described below
    :param kwargs: The keyword arguments are passed to the importer
     function
    :return: A BEL graph.

    This is the universal loader, which means any file
    path can be given and PyBEL will look up the appropriate
    load function. Allowed extensions are:

    - bel
    - bel.nodelink.json
    - bel.cx.json
    - bel.jgif.json

    The previous extensions also support gzipping.
    Other allowed extensions that don't support gzip are:

    - bel.pickle / bel.gpickle / bel.pkl
    - indra.json
    """
    for extension, importer in IMPORTERS.items():
        if path.endswith(extension):
            return importer(path, **kwargs)
    raise InvalidExtensionError(path=path)


def dump(graph: BELGraph, path: str, **kwargs) -> None:
    """Write a BEL graph.

    :param graph: A BEL graph
    :param path: The path to which the BEL graph is written.
    :param kwargs: The keyword arguments are passed to the exporter
     function

    This is the universal loader, which means any file
    path can be given and PyBEL will look up the appropriate
    writer function. Allowed extensions are:

    - bel
    - bel.nodelink.json
    - bel.unodelink.json
    - bel.cx.json
    - bel.jgif.json
    - bel.graphdati.json

    The previous extensions also support gzipping.
    Other allowed extensions that don't support gzip are:

    - bel.pickle / bel.gpickle / bel.pkl
    - indra.json
    - tsv
    - gsea
    """
    for extension, exporter in EXPORTERS.items():
        if path.endswith(extension):
            return exporter(graph, path, **kwargs)
    raise InvalidExtensionError(path=path)
