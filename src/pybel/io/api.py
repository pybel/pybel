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

    def __init__(self, name):
        fname = os.path.basename(name)
        super().__init__('Invalid extension for file: {}'.format(fname))


@open_file(0, mode='r')
def load(file: Union[str, TextIO], **kwargs) -> BELGraph:
    """Read a BEL graph."""
    name = file.name
    for extension, importer in IMPORTERS.items():
        if name.endswith(extension):
            return importer(file, **kwargs)
    raise InvalidExtensionError(name=name)


@open_file(1, mode='w')
def dump(graph: BELGraph, file: Union[str, TextIO], **kwargs) -> None:
    """Write a BEL graph."""
    name = file.name
    for extension, exporter in EXPORTERS.items():
        if name.endswith(extension):
            return exporter(graph, file, **kwargs)
    raise InvalidExtensionError(name=name)
