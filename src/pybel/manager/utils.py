# -*- coding: utf-8 -*-

"""Utilities for the PyBEL database manager."""

from typing import Dict, Mapping, Optional, Tuple, Union

from ..utils import parse_datetime


def extract_shared_required(config, definition_header: str = 'Namespace'):
    """Get the required annotations shared by BEL namespace and annotation resource documents.

    :param dict config: The configuration dictionary representing a BEL resource
    :param definition_header: ``Namespace`` or ``AnnotationDefinition``
    :rtype: dict
    """
    return {
        'keyword': config[definition_header]['Keyword'],
        'created': parse_datetime(config[definition_header]['CreatedDateTime']),
    }


def extract_shared_optional(bel_resource, definition_header: str = 'Namespace'):
    """Get the optional annotations shared by BEL namespace and annotation resource documents.

    :param dict bel_resource: A configuration dictionary representing a BEL resource
    :param definition_header: ``Namespace`` or ``AnnotationDefinition``
    :rtype: dict
    """
    shared_mapping = {
        'description': (definition_header, 'DescriptionString'),
        'version': (definition_header, 'VersionString'),
        'author': ('Author', 'NameString'),
        'license': ('Author', 'CopyrightString'),
        'contact': ('Author', 'ContactInfoString'),
        'citation': ('Citation', 'NameString'),
        'citation_description': ('Citation', 'DescriptionString'),
        'citation_version': ('Citation', 'PublishedVersionString'),
        'citation_url': ('Citation', 'ReferenceURL'),
    }

    result = {}

    update_insert_values(bel_resource, shared_mapping, result)

    if 'PublishedDate' in bel_resource.get('Citation', {}):
        result['citation_published'] = parse_datetime(bel_resource['Citation']['PublishedDate'])

    return result


def update_insert_values(bel_resource: Mapping, mapping: Mapping[str, Tuple[str, str]], values: Dict[str, str]) -> None:
    """Update the value dictionary with a BEL resource dictionary."""
    for database_column, (section, key) in mapping.items():
        if section in bel_resource and key in bel_resource[section]:
            values[database_column] = bel_resource[section][key]


def int_or_str(v: Optional[str]) -> Union[None, int, str]:
    """Safe converts an string represent an integer to an integer or passes through ``None``."""
    if v is None:
        return
    try:
        return int(v)
    except ValueError:
        return v
