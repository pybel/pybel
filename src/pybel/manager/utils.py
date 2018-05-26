# -*- coding: utf-8 -*-

from ..utils import parse_datetime


def extract_shared_required(config, definition_header='Namespace'):
    """Gets the required annotations shared by BEL namespace and annotation resource documents

    :param dict config: The configuration dictionary representing a BEL resource
    :param str definition_header: ``Namespace`` or ``AnnotationDefinition``
    :rtype: dict
    """
    return {
        'keyword': config[definition_header]['Keyword'],
        'created': parse_datetime(config[definition_header]['CreatedDateTime']),
        'author': config['Author']['NameString'],
        'citation': config['Citation']['NameString']
    }


def update_insert_values(bel_resource, m, d):
    for database_column, (section, key) in m.items():
        if section in bel_resource and key in bel_resource[section]:
            d[database_column] = bel_resource[section][key]


def extract_shared_optional(bel_resource, definition_header='Namespace'):
    """Gets the optional annotations shared by BEL namespace and annotation resource documents
    
    :param dict bel_resource: A configuration dictionary representing a BEL resource
    :param str definition_header: ``Namespace`` or ``AnnotationDefinition``
    :rtype: dict
    """
    shared_mapping = {
        'description': (definition_header, 'DescriptionString'),
        'version': (definition_header, 'VersionString'),
        'license': ('Author', 'CopyrightString'),
        'contact': ('Author', 'ContactInfoString'),
        'citation_description': ('Citation', 'DescriptionString'),
        'citation_version': ('Citation', 'PublishedVersionString'),
        'citation_url': ('Citation', 'ReferenceURL')
    }

    result = {}

    update_insert_values(bel_resource, shared_mapping, result)

    if 'PublishedDate' in bel_resource['Citation']:
        result['citation_published'] = parse_datetime(bel_resource['Citation']['PublishedDate'])

    return result


def int_or_str(v):
    """Safe converts an string represent an integer to an integer. If it's none, returns none

    :param v:
    :return:
    """
    if v is None:
        return
    try:
        return int(v)
    except Exception:
        return v
