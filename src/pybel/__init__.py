# -*- coding: utf-8 -*-

"""Parsing, validation, compilation, and data exchange of Biological Expression Language (BEL)."""

from .canonicalize import edge_to_bel, to_bel_script, to_bel_script_gz, to_bel_script_lines
from .dsl import BaseAbundance, BaseEntity
from .io import *
from .io.api import dump, load
from .manager import Manager, from_database, to_database
from .struct import BELGraph, Pipeline, Query
from .struct.operations import union
from .version import get_version
