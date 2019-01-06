# -*- coding: utf-8 -*-

"""Utilities for downloading, reading, and writing BEL script, namespace files, and annotation files."""

from .exc import EmptyResourceError, InvalidResourceError, MissingResourceError, ResourceError
from .read_document import split_file_to_annotations_and_definitions
from .read_utils import get_bel_resource, get_lines, parse_bel_resource
from .write_annotation import write_annotation
from .write_document import make_knowledge_header
from .write_namespace import write_namespace
