# -*- coding: utf-8 -*-

import re

METADATA_LINE_RE = re.compile("(SET\s+DOCUMENT|DEFINE\s+NAMESPACE|DEFINE\s+ANNOTATION)")

citation_format = 'SET Citation = {{"PubMed","{}","{}"}}'
evidence_format = 'SET Evidence = "{}"'

NAMESPACE_URL_FMT = 'DEFINE NAMESPACE {} AS URL "{}"'
NAMESPACE_PATTERN_FMT = 'DEFINE NAMESPACE {} AS PATTERN "{}"'
ANNOTATION_URL_FMT = 'DEFINE ANNOTATION {} AS URL "{}"'
ANNOTATION_PATTERN_FMT = 'DEFINE ANNOTATION {} AS PATTERN "{}"'


def format_annotation_list(annotation, values):
    return 'DEFINE ANNOTATION {} AS LIST {{{}}}'.format(annotation, ', '.join('"{}"'.format(e) for e in values))
