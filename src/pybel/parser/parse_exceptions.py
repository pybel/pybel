# -*- coding: utf-8 -*-
from ..exceptions import PyBelWarning


# Naming Warnings

class NakedNameWarning(PyBelWarning):
    """Raised when there is an identifier without a namespace. Enable lenient mode to suppress"""


class MissingDefaultNameWarning(PyBelWarning):
    """Raised if reference to value not in default namespace"""


class UndefinedNamespaceWarning(PyBelWarning):
    """Raised if reference made to undefined namespace"""


class MissingNamespaceNameWarning(PyBelWarning):
    """Raised if reference to value not in namespace"""


class UndefinedAnnotationWarning(PyBelWarning):
    """Raised when an undefined annotation is used"""


class MissingAnnotationKeyWarning(PyBelWarning):
    """Raised when trying to unset an annotation that is not set"""


class IllegalAnnotationValueWarning(PyBelWarning):
    """Raised when an annotation has a value that does not belong to the original set of valid annotation values."""


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


class InvalidCitationException(PyBelWarning):
    """Raised when the format for a citation is wrong. It should have either {type, name, reference}; or
        {type, name, reference, date, authors, comments}"""


class MissingCitationException(PyBelWarning):
    """Tried to add an edge, but no citation present. Most likely due to previous improperly formatted citation"""


class MissingSupportWarning(PyBelWarning):
    """All BEL statements must be qualified with evidence"""


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
