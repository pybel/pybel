# -*- coding: utf-8 -*-

"""
A message for "General Parser Failure" is displayed when a problem was caused due to an unforseen error. The line
number and original statement are printed for the user to debug.
"""

from ..exceptions import PyBelWarning


# TODO refactor code with this class
class PyBelParserWarning(PyBelWarning):
    """Base PyBEL parser exception, which holds the line and position where a parsing problem occurred"""

    def __init__(self, line, position):
        super(PyBelParserWarning, self).__init__(line, position)
        self.line = line
        self.position = position


# Naming Warnings

class NakedNameWarning(PyBelWarning):
    """Raised when there is an identifier without a namespace. Enable lenient mode to suppress"""

    def __init__(self, line, position, name):
        PyBelWarning.__init__(self, line, position, name)
        self.line = line
        self.position = position
        self.name = name

    def __str__(self):
        return '[pos:{}] "{}" should be qualified with a valid namespace'.format(self.position, self.name)


class MissingDefaultNameWarning(PyBelWarning):
    """Raised if reference to value not in default namespace"""

    def __init__(self, name):
        PyBelWarning.__init__(self, name)
        self.name = name

    def __str__(self):
        return '"{}" is not in the default namespace'.format(self.name)


class UndefinedNamespaceWarning(PyBelWarning):
    """Raised if reference made to undefined namespace"""

    def __init__(self, namespace):
        PyBelWarning.__init__(self, namespace)
        self.namespace = namespace

    def __str__(self):
        return '"{}" is not a defined namespace'.format(self.namespace)


class IdentifierWarning(PyBelWarning):
    """The base class for warnings related to namespace:name identifiers"""

    def __init__(self, name, namespace):
        PyBelWarning.__init__(self, name, namespace)
        self.name = name
        self.namespace = namespace


class MissingNamespaceNameWarning(IdentifierWarning):
    """Raised if reference to value not in namespace"""

    def __str__(self):
        return '"{}" is not in the {} namespace'.format(self.name, self.namespace)


class MissingNamespaceRegexWarning(IdentifierWarning):
    """Raised if reference not matching regex"""

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
        return '"{}" is not defined in the {} annotation'.format(self.value, self.annotation)


class MissingAnnotationRegexWarning(PyBelWarning):
    """Raised if annotation doesn't match regex"""

    def __init__(self, value, annotation):
        PyBelWarning.__init__(self, value, annotation)
        self.value = value
        self.annotation = annotation

    def __str__(self):
        return '''"{}" doesn't match the regex for {} annotation'''.format(self.value, self.annotation)


# Provenance Warnings

class VersionFormatWarning(PyBelWarning):
    """Raised if the version string doesn't adhere to semantic versioning or YYYYMMDD format"""

    def __init__(self, version_string):
        PyBelWarning.__init__(self, version_string)
        self.version_string = version_string

    def __str__(self):
        return '''Version string "{}" neither is a date like YYYYMMDD nor adheres to semantic versioning'''.format(
            self.version_string)


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

.. seealso:: BEL 1.0 specification on the `properties section <http://openbel.org/language/web/version_1.0/bel_specification_version_1.0.html#_properties_section>`_
    """

    def __init__(self, key, value):
        PyBelWarning.__init__(self, key, value)
        self.key = key
        self.value = value

    def __str__(self):
        return 'Invalid document metadata key: {}'.format(self.key)


class MissingMetadataException(PyBelWarning):
    """BEL Script is missing critical metadata"""

    def __init__(self, key):
        PyBelWarning.__init__(self, key)
        self.key = key

    def __str__(self):
        return 'Missing required document metadata: {}'.format(self.key)


class InvalidCitationLengthException(PyBelWarning):
    """Raised when the format for a citation is wrong"""

    def __init__(self, line, position):
        PyBelWarning.__init__(self, line, position)
        self.line = line
        self.position = position


class CitationTooShortException(InvalidCitationLengthException):
    """Raised when a citation does not have the minimum of {type, name, reference}"""

    def __str__(self):
        return "[pos:{}] Citation is missing required fields: {}".format(self.position, self.line)


class CitationTooLongException(InvalidCitationLengthException):
    """Raised when a citation has more than the allowed entries, {type, name, reference, date, authors, comments}"""

    def __str__(self):
        return "[pos:{}] Citation contains too many entries: {}".format(self.position, self.line)


class MissingCitationException(PyBelWarning):
    """Tried to parse a line, but no citation present. Most likely due to previous improperly formatted citation"""

    def __init__(self, line):
        """

        :param line: The line of the BEL document that's a problem
        :type line: str
        """
        PyBelWarning.__init__(self, line)
        self.line = line

    def __str__(self):
        return "Missing citation; can't add: {}".format(self.line)


class MissingSupportWarning(PyBelWarning):
    """All BEL statements must be qualified with evidence"""

    def __init__(self, line):
        """

        :param line: The line of the BEL document that's a problem
        :type line: str
        """
        PyBelWarning.__init__(self, line)
        self.string = line

    def __str__(self):
        return "Missing evidence; can't add: {}".format(self.string)


class InvalidCitationType(PyBelWarning):
    """Incorrect type of citation. Should be one of:

- Book
- PubMed
- Journal
- Online Resource
- Other

.. seealso:: OpenBEL wiki on `citations <https://wiki.openbel.org/display/BELNA/Citation>`_
    """

    def __init__(self, line, position, citation_type):
        PyBelWarning.__init__(self, line, position, citation_type)
        self.line = line
        self.position = position
        self.citation_type = citation_type

    def __str__(self):
        return '[pos:{}] "{}" is not a valid citation type'.format(self.position, self.citation_type)


class InvalidPubMedIdentifierWarning(PyBelWarning):
    """Tried to make a citation to PubMed that's not a legal PMID"""

    def __init__(self, line, position, reference):
        PyBelWarning.__init__(self, line, position, reference)
        self.line = line
        self.position = position
        self.reference = reference

    def __str__(self):
        return '[pos:{}] "{}" is not a valid PMID'.format(self.position, self.reference)


# BEL Syntax Warnings

class MalformedTranslocationWarning(PyBelWarning):
    """Raised when there is a translocation statement without location information."""

    def __init__(self, line, tokens, position):
        PyBelWarning.__init__(self, line, position, tokens)
        self.line = line
        self.position = position
        self.tokens = tokens

    def __str__(self):
        return '[pos:{}] Unqualified translocation: {} {}'.format(self.position, self.line, self.tokens)


class PlaceholderAminoAcidWarning(PyBelWarning):
    """X might be used as a placeholder amino acid, or as a colloquial signifier for a truncation at a certain position.
     Neither are valid within the HGVS nomenclature that defines the way variations are encoded in BEL."""

    def __init__(self, line, position, code):
        PyBelWarning.__init__(self, line, position, code)
        self.line = line
        self.position = position
        self.code = code

    def __str__(self):
        return '[pos:{}] Placeholder amino acid found: {}'.format(self.position, self.code)


class NestedRelationWarning(PyBelWarning):
    """Raised when encountering a nested statement. See our the docs for an explanation of why we explicitly
        do not support nested statements."""

    def __init__(self, message):
        PyBelWarning.__init__(self, message)
        self.message = message

    def __str__(self):
        return 'Nesting is not supported. Split this statement: {}'.format(self.message)


class LexicographyWarning(PyBelWarning):
    """Raised when encountering improper capitalization of namespace/annotation names"""


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
        return "{} {}:{} should be encoded as one of: {}".format(self.function,
                                                                 self.namespace,
                                                                 self.name,
                                                                 ', '.join(self.allowed_functions))


class RelabelWarning(PyBelWarning):
    """Raised when a node is relabeled"""

    def __init__(self, node, old_label, new_label):
        PyBelWarning.__init__(self, node, old_label, new_label)
        self.node = node
        self.old_label = old_label
        self.new_label = new_label

    def __str__(self):
        return 'Tried to relabel {} from {} to {}'.format(self.node, self.old_label, self.new_label)
