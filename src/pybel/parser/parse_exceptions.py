# -*- coding: utf-8 -*-
from ..exceptions import PyBelWarning


# Naming Warnings

class NakedNameWarning(PyBelWarning):
    """Raised when there is an identifier without a namespace. Enable lenient mode to suppress"""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return '"{}" should be qualified with a valid namespace'.format(self.name)


class MissingDefaultNameWarning(PyBelWarning):
    """Raised if reference to value not in default namespace"""


class UndefinedNamespaceWarning(PyBelWarning):
    """Raised if reference made to undefined namespace"""


class MissingNamespaceNameWarning(PyBelWarning):
    """Raised if reference to value not in namespace"""

    def __init__(self, name, namespace):
        self.name = name
        self.namespace = namespace

    def __str__(self):
        return '"{}" is not in the {} namespace'.format(self.name, self.namespace)


class UndefinedAnnotationWarning(PyBelWarning):
    """Raised when an undefined annotation is used"""


class MissingAnnotationKeyWarning(PyBelWarning):
    """Raised when trying to unset an annotation that is not set"""

    def __init__(self, annotation):
        self.annotation = annotation

    def __str__(self):
        return '''"{}" is not set, so it can't be unset'''.format(self.annotation)


class IllegalAnnotationValueWarning(PyBelWarning):
    """Raised when an annotation has a value that does not belong to the original set of valid annotation values."""

    def __init__(self, value, annotation):
        self.value = value
        self.annotation = annotation

    def __str__(self):
        return '"{}" is not in the {} annotation'.format(self.value, self.annotation)


# Provenance Warnings

class InvalidMetadataException(PyBelWarning):
    """Illegal document metadata. Should be one of:

- Authors
- ContactInfo
- Copyright
- Description
- Disclaimer
- Licenses
- Name
- Version

See also: http://openbel.org/language/web/version_1.0/bel_specification_version_1.0.html#_properties_section
    """


class MissingMetadataException(PyBelWarning):
    """BEL Script is missing critical metadata"""

class InvalidCitationException(PyBelWarning):
    """Raised when the format for a citation is wrong. It should have either {type, name, reference}; or
        {type, name, reference, date, authors, comments}"""


class MissingCitationException(PyBelWarning):
    """Tried to add an edge, but no citation present. Most likely due to previous improperly formatted citation"""


class MissingSupportWarning(PyBelWarning):
    """All BEL statements must be qualified with evidence"""


class InvalidCitationType(PyBelWarning):
    """Incorrect type of citation. Should be one of:

- "Book"
- "PubMed"
- "Journal"
- "Online Resource"
- "Other"

See also: https://wiki.openbel.org/display/BELNA/Citation
    """

    def __init__(self, citation_type):
        self.citation_type = citation_type

    def __str__(self):
        return '{} is not a valid citation type'.format(self.citation_type)


class InvalidPubMedIdentifierWarning(PyBelWarning):
    """Tried to make a citation to PubMed that's not a legal PMID"""

    def __init__(self, reference):
        self.reference = reference

    def __str__(self):
        return '{} is not a valid PMID'.format(self.reference)


# BEL Syntax Warnings

class MalformedTranslocationWarning(PyBelWarning):
    """Raised when there is a translocation statement without location information."""


class PlaceholderAminoAcidWarning(PyBelWarning):
    """X might be used as a placeholder amino acid, or as a colloquial signifier for a truncation at a certain position.
     Neither are valid within the HGVS nomenclature that defines the way variations are encoded in BEL."""


class NestedRelationWarning(PyBelWarning):
    """Raised when encountering a nested statement. See our the docs for an explanation of why we explicitly
        do not support nested statements."""


class LexicographyWarning(PyBelWarning):
    """Improper capitalization"""


# Semantic Warnings

class InvalidFunctionSemantic(PyBelWarning):
    """Used an identifier in a semantically invalid function"""
