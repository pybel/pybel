# -*- coding: utf-8 -*-

"""Constants for reading and writing BEL script, namespace files, and annotation files."""

import re

METADATA_LINE_RE = re.compile(r"(SET\s+DOCUMENT|DEFINE\s+NAMESPACE|DEFINE\s+ANNOTATION)")

citation_format = 'SET Citation = {{"PubMed","{}","{}"}}'
evidence_format = 'SET Evidence = "{}"'

NAMESPACE_URL_FMT = 'DEFINE NAMESPACE {} AS URL "{}"'
NAMESPACE_PATTERN_FMT = 'DEFINE NAMESPACE {} AS PATTERN "{}"'
ANNOTATION_URL_FMT = 'DEFINE ANNOTATION {} AS URL "{}"'
ANNOTATION_PATTERN_FMT = 'DEFINE ANNOTATION {} AS PATTERN "{}"'
ANNOTATION_LIST_FMT = 'DEFINE ANNOTATION {} AS LIST {{{}}}'


def format_annotation_list(annotation, values):
    """Generate an annotation list definition.

    :param str annotation: The name of the annotation
    :param iter[str] values: The values for the annotation
    :rtype: str
    """
    return ANNOTATION_LIST_FMT.format(annotation, ', '.join('"{}"'.format(e) for e in values))
