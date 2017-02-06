# -*- coding: utf-8 -*-

"""
A message for "General Parser Failure" is displayed when a problem was caused due to an unforseen error. The line
number and original statement are printed for the user to debug.

When errors in the statement leave the term or relation as nonsense, these errors are thrown and the statement is
excluded. These are logged at the ERROR level with code :code:`PyBEL1XX`.
"""

from ..exceptions import PyBelWarning


# Naming Warnings

class NakedNameWarning(PyBelWarning):
    """Raised when there is an identifier without a namespace. Enable lenient mode to suppress"""

    def __init__(self, name):
        PyBelWarning.__init__(self, name)
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
        PyBelWarning.__init__(self, name, namespace)
        self.name = name
        self.namespace = namespace

    def __str__(self):
        return '"{}" is not in the {} namespace'.format(self.name, self.namespace)


class MissingNamespaceRegexWarning(PyBelWarning):
    """Raised if reference not matching regex"""

    def __init__(self, name, namespace):
        PyBelWarning.__init__(self, name, namespace)
        self.name = name
        self.namespace = namespace

    def __str__(self):
        return '''"{}" doesn't match the regex for {} namespace'''.format(self.name, self.namespace)


class UndefinedAnnotationWarning(PyBelWarning):
    """Raised when an undefined annotation is used"""

    def __init__(self, annotation):
        PyBelWarning.__init__(self, annotation)
        self.annotation = annotation

    def __str__(self):
        return '''"{}" is not defined'''.format(self.annotation)


class MissingAnnotationKeyWarning(PyBelWarning):
    """Raised when trying to unset an annotation that is not set"""

    def __init__(self, annotation):
        PyBelWarning.__init__(self, annotation)
        self.annotation = annotation

    def __str__(self):
        return '''"{}" is not set, so it can't be unset'''.format(self.annotation)


class IllegalAnnotationValueWarning(PyBelWarning):
    """Raised when an annotation has a value that does not belong to the original set of valid annotation values."""

    def __init__(self, value, annotation):
        PyBelWarning.__init__(self, value, annotation)
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

    def __init__(self, citation):
        PyBelWarning.__init__(self, citation)
        self.citation = citation

    def __str__(self):
        return "Invalid citation, missing required fields: {}".format(self.citation)


class MissingCitationException(PyBelWarning):
    """Tried to add an edge, but no citation present. Most likely due to previous improperly formatted citation"""

    def __init__(self, citation):
        PyBelWarning.__init__(self, citation)
        self.citation = citation

    def __str__(self):
        return "Missing citation; can't add: {}".format(self.citation)


class MissingSupportWarning(PyBelWarning):
    """All BEL statements must be qualified with evidence"""

    def __init__(self, string):
        PyBelWarning.__init__(self, string)
        self.string = string

    def __str__(self):
        return "Missing evidence; can't add: {}".format(self.string)


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
        PyBelWarning.__init__(self, citation_type)
        self.citation_type = citation_type

    def __str__(self):
        return '{} is not a valid citation type'.format(self.citation_type)


class InvalidPubMedIdentifierWarning(PyBelWarning):
    """Tried to make a citation to PubMed that's not a legal PMID"""

    def __init__(self, reference):
        PyBelWarning.__init__(self, reference)
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

    def __init__(self, message):
        PyBelWarning.__init__(self, message)
        self.message = message

    def __str__(self):
        return 'Nesting is not supported. Split this statement: {}'.format(self.message)


class LexicographyWarning(PyBelWarning):
    """Improper capitalization"""


# Semantic Warnings

class InvalidFunctionSemantic(PyBelWarning):
    """Used an identifier in a semantically invalid function"""

    def __init__(self, function, namespace, name, allowed_functions):
        PyBelWarning.__init__(self, function, namespace, name, allowed_functions)
        self.function = function
        self.namespace = namespace
        self.name = name
        self.allowed_functions = allowed_functions

    def __str__(self):
        return "{}:{} should be encoded as one of: {}".format(self.namespace,
                                                              self.name,
                                                              ', '.join(self.allowed_functions))
