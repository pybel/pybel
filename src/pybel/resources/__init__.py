# -*- coding: utf-8 -*-

"""Utilities for downloading, reading, and writing BEL script, namespace files, and annotation files."""

import warnings

from bel_resources import (
    EmptyResourceError, InvalidResourceError, MissingResourceError, ResourceError,
    get_bel_resource, get_lines, make_knowledge_header, parse_bel_resource, split_file_to_annotations_and_definitions,
    write_annotation, write_namespace,
)

__all__ = [
    'EmptyResourceError',
    'InvalidResourceError',
    'MissingResourceError',
    'ResourceError',
    'split_file_to_annotations_and_definitions',
    'get_bel_resource',
    'get_lines',
    'parse_bel_resource',
    'write_annotation',
    'make_knowledge_header',
    'write_namespace',
]

warnings.warn('Use the bel_resources package instead of pybel.resources. Will be removed in 0.14.0', DeprecationWarning)
