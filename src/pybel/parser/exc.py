# -*- coding: utf-8 -*-

"""Exceptions for the BEL parser.

A message for "General Parser Failure" is displayed when a problem was caused due to an unforseen error. The line
number and original statement are printed for the user to debug.
"""

from ..exceptions import PyBelWarning


class PyBelParserWarning(PyBelWarning):
    """Base PyBEL parser exception, which holds the line and position where a parsing problem occurred"""

    def __init__(self, line_number, line, position, *args):
        """
        :param int line_number: The line number on which this warning occurred
        :param str line: The content of the line
        :param int position: The position within the line where the warning occurred
        :param args: Additional arguments to supply to the super class
        """
        super(PyBelParserWarning, self).__init__(line_number, line, position, *args)
        self.line_number = line_number
        self.line = line
        self.position = position

    def __str__(self):
        return 'General Parser Failure on line {} at pos {}: {}'.format(self.line_number, self.position, self.line)


class BelSyntaxError(PyBelParserWarning, SyntaxError):
    """For general syntax errors"""


class InconsistentDefinitionError(PyBelParserWarning):
    """Base PyBEL error for redefinition"""

    def __init__(self, line_number, line, position, definition):
        super(InconsistentDefinitionError, self).__init__(line_number, line, position, definition)
        self.definition = definition

    def __str__(self):
        return 'Tried to redefine {} with: {}'.format(self.definition, self.line)


class RedefinedNamespaceError(InconsistentDefinitionError):
    """Raised when a namespace is redefined"""


class RedefinedAnnotationError(InconsistentDefinitionError):
    """Raised when an annotation is redefined"""


# Naming Warnings

class NameWarning(PyBelParserWarning):
    """The base class for errors related to nomenclature."""

    def __init__(self, line_number, line, position, name, *args):
        """Build a NameWarning.

        :param int line_number: The line number on which the warning occurred
        :param str line: The line on which the warning occurred
        :param int position: The position in the line that caused the warning
        :param str name: The name that caused the warning
        """
        super(NameWarning, self).__init__(line_number, line, position, name, *args)
        self.name = name


class NakedNameWarning(NameWarning):
    """Raised when there is an identifier without a namespace. Enable lenient mode to suppress"""

    def __str__(self):
        return '[pos:{}] "{}" should be qualified with a valid namespace'.format(self.position, self.name)


class MissingDefaultNameWarning(NameWarning):
    """Raised if reference to value not in default namespace"""

    def __str__(self):
        return '"{}" is not in the default namespace'.format(self.name)


class NamespaceIdentifierWarning(NameWarning):
    """The base class for warnings related to namespace:name identifiers"""

    def __init__(self, line_number, line, position, namespace, name):
        """
        :param int line_number: The line number of the line that caused the exception
        :param str line: The line that caused the exception
        :param int position: The line's position of the exception
        :param str namespace: The namespace of the identifier
        :param str name: The name of the identifier
        """
        super(NamespaceIdentifierWarning, self).__init__(line_number, line, position, name, namespace)
        self.namespace = namespace


class UndefinedNamespaceWarning(NamespaceIdentifierWarning):
    """Raised if reference made to undefined namespace"""

    def __str__(self):
        return '"{}" is not a defined namespace'.format(self.namespace)


class MissingNamespaceNameWarning(NamespaceIdentifierWarning):
    """Raised if reference to value not in namespace"""

    def __str__(self):
        return '"{}" is not in the {} namespace'.format(self.name, self.namespace)


class MissingNamespaceRegexWarning(NamespaceIdentifierWarning):
    """Raised if reference not matching regex"""

    def __str__(self):
        return '''"{}" doesn't match the regex for {} namespace'''.format(self.name, self.namespace)


class AnnotationWarning(PyBelParserWarning):
    """Base exception for annotation warnings"""

    def __init__(self, line_number, line, position, annotation, *args):
        """Build an AnnotationWarning.

        :param int line_number: The line number on which the warning occurred
        :param str line: The line on which the warning occurred
        :param int position: The position in the line that caused the warning
        :param str annotation: The annotation name that caused the warning
        """
        super(AnnotationWarning, self).__init__(line_number, line, position, annotation, *args)
        self.annotation = annotation


class UndefinedAnnotationWarning(AnnotationWarning):
    """Raised when an undefined annotation is used"""

    def __str__(self):
        return '''"{}" is not defined'''.format(self.annotation)


class MissingAnnotationKeyWarning(AnnotationWarning):
    """Raised when trying to unset an annotation that is not set"""

    def __str__(self):
        return '''"{}" is not set, so it can't be unset'''.format(self.annotation)


class AnnotationIdentifierWarning(AnnotationWarning):
    """Base exception for annotation:value pairs"""

    def __init__(self, line_number, line, position, annotation, value):
        super(AnnotationIdentifierWarning, self).__init__(line_number, line, position, annotation, value)
        self.value = value


class IllegalAnnotationValueWarning(AnnotationIdentifierWarning):
    """Raised when an annotation has a value that does not belong to the original set of valid annotation values."""

    def __str__(self):
        return '"{}" is not defined in the {} annotation'.format(self.value, self.annotation)


class MissingAnnotationRegexWarning(AnnotationIdentifierWarning):
    """Raised if annotation doesn't match regex"""

    def __str__(self):
        return '''"{}" doesn't match the regex for {} annotation'''.format(self.value, self.annotation)


# Provenance Warnings

class VersionFormatWarning(PyBelParserWarning):
    """Raised if the version string doesn't adhere to semantic versioning or ``YYYYMMDD`` format"""

    def __init__(self, line_number, line, position, version_string):
        super(VersionFormatWarning, self).__init__(line_number, line, position, version_string)
        self.version_string = version_string

    def __str__(self):
        return (
            'Version string "{}" neither is a date like YYYYMMDD nor adheres to semantic versioning.'
            ' See http://semver.org/'.format(self.version_string)
        )


class MetadataException(PyBelWarning):
    """Base exception for issues with document metadata"""

    def __init__(self, line_number, line, *args):
        super(MetadataException, self).__init__(line_number, line, *args)
        self.line = line
        self.line_number = line_number

    def __str__(self):
        return '[line:{}] Invalid metadata - "{}"'.format(self.line_number, self.line)


class MalformedMetadataException(MetadataException):
    """Raised when an invalid metadata line is encountered"""


class InvalidMetadataException(PyBelParserWarning):
    """Raised when an incorrect document metadata key is used. Valid document metadata keys are:

- ``Authors``
- ``ContactInfo``
- ``Copyright``
- ``Description``
- ``Disclaimer``
- ``Licenses``
- ``Name``
- ``Version``

.. seealso:: BEL specification on the `properties section <http://openbel.org/language/web/version_1.0/bel_specification_version_1.0.html#_properties_section>`_
    """

    def __init__(self, line_number, line, position, key, value):
        super(InvalidMetadataException, self).__init__(line_number, line, position, key, value)
        self.key = key
        self.value = value

    def __str__(self):
        return 'Invalid document metadata key: {}'.format(self.key)


class MissingMetadataException(PyBelWarning):
    """Raised when a BEL Script is missing critical metadata."""

    def __init__(self, key):
        super(MissingMetadataException, self).__init__(key)
        self.key = key

    def __str__(self):
        return 'Missing required document metadata: {}'.format(self.key)


class InvalidCitationLengthException(PyBelParserWarning):
    """Base exception raised when the format for a citation is wrong."""


class CitationTooShortException(InvalidCitationLengthException):
    """Raised when a citation does not have the minimum of {type, name, reference}."""

    def __str__(self):
        return "[pos:{}] Citation is missing required fields: {}".format(self.position, self.line)


class CitationTooLongException(InvalidCitationLengthException):
    """Raised when a citation has more than the allowed entries, {type, name, reference, date, authors, comments}."""

    def __str__(self):
        return "[pos:{}] Citation contains too many entries: {}".format(self.position, self.line)


class MissingCitationException(PyBelParserWarning):
    """Raised when trying to parse a BEL statement, but no citation is currently set. This might be due to a previous
    error in the formatting of a citation.

    Though it's not a best practice, some BEL curators set other annotations before the citation. If this is the case
    in your BEL document, and you're absolutly sure that all UNSET statements are correctly written, you can use
    ``citation_clearing=True`` as a keyword argument in any of the IO functions in :func:`pybel.from_lines`,
    :func:`pybel.from_url`, or :func:`pybel.from_path`.
    """

    def __str__(self):
        return "Missing citation; can't add: {}".format(self.line)


class MissingSupportWarning(PyBelParserWarning):
    """Raised when trying to parse a BEL statement, but no evidence is currently set. All BEL statements must be
    qualified with evidence.

    If your data is serialized from a database and provenance information is not readily
    accessible, consider referencing the publication for the database, or a url pointing to the data from either
    a programmatically or human-readable endpoint.
    """

    def __str__(self):
        return "Missing evidence; can't add: {}".format(self.line)


class MissingAnnotationWarning(PyBelParserWarning):
    """Raised when trying to parse a BEL statement and a required annotation is not present."""

    def __init__(self, line_number, line, position, required_annotations):
        super(MissingAnnotationWarning, self).__init__(line_number, line, position, required_annotations)
        self.required_annotations = required_annotations

    def __str__(self):
        return 'Missing annotations: {}'.format(', '.join(sorted(self.required_annotations)))


class InvalidCitationType(PyBelParserWarning):
    """Raise when a citation is set with an incorrect type. Valid citation types include:

- ``Book``
- ``PubMed``
- ``Journal``
- ``Online Resource``
- ``URL``
- ``DOI``
- ``Other``

.. seealso:: OpenBEL wiki on `citations <https://wiki.openbel.org/display/BELNA/Citation>`_
    """

    def __init__(self, line_number, line, position, citation_type):
        super(InvalidCitationType, self).__init__(line_number, line, position, citation_type)
        self.citation_type = citation_type

    def __str__(self):
        return '[pos:{}] "{}" is not a valid citation type'.format(self.position, self.citation_type)


class InvalidPubMedIdentifierWarning(PyBelParserWarning):
    """Raised when a citation is set whose type is ``PubMed`` but whose database identifier is not a valid integer."""

    def __init__(self, line_number, line, position, reference):
        super(InvalidPubMedIdentifierWarning, self).__init__(line_number, line, position, reference)
        self.reference = reference

    def __str__(self):
        return '[pos:{}] "{}" is not a valid PubMed identifier'.format(self.position, self.reference)


# BEL Syntax Warnings

class MalformedTranslocationWarning(PyBelParserWarning):
    """Raised when there is a translocation statement without location information."""

    def __init__(self, line_number, line, position, tokens):
        super(MalformedTranslocationWarning, self).__init__(line_number, line, position, tokens)
        self.tokens = tokens

    def __str__(self):
        return '[pos:{}] Unqualified translocation: {} {}'.format(self.position, self.line, self.tokens)


class PlaceholderAminoAcidWarning(PyBelParserWarning):
    """Raised when an invalid amino acid code is given.


    One example might be the usage of X, which is a colloquial signifier for a truncation in a given position. Text
    mining efforts for knowledge extraction make this mistake often. X might also signify a placeholder amino acid.
    """

    def __init__(self, line_number, line, position, code):
        super(PlaceholderAminoAcidWarning, self).__init__(line_number, line, position, code)
        self.code = code

    def __str__(self):
        return '[pos:{}] Placeholder amino acid found: {}'.format(self.position, self.code)


class NestedRelationWarning(PyBelParserWarning):
    """Raised when encountering a nested statement. See our the docs for an explanation of why we explicitly
    do not support nested statements.
    """

    def __str__(self):
        return 'Nesting is not supported. Split this statement: {}'.format(self.line)


class LexicographyWarning(PyBelWarning):
    """Raised when encountering improper capitalization of namespace/annotation names."""


# Semantic Warnings

class InvalidFunctionSemantic(PyBelParserWarning):
    """Raised when an invalid function is used for a given node.

    For example, an HGNC symbol for a protein-coding gene YFG cannot be referenced as an miRNA with ``m(HGNC:YFG)``
    """

    def __init__(self, line_number, line, position, function, namespace, name, allowed_functions):
        super(InvalidFunctionSemantic, self).__init__(line_number, line, position, function, namespace, name,
                                                      allowed_functions)
        self.function = function
        self.namespace = namespace
        self.name = name
        self.allowed_functions = allowed_functions

    def __str__(self):
        return "{} {}:{} should be encoded as one of: {}".format(
            self.function,
            self.namespace,
            self.name,
            ', '.join(self.allowed_functions)
        )


class RelabelWarning(PyBelParserWarning):
    """Raised when a node is relabeled"""

    def __init__(self, line_number, line, position, node, old_label, new_label):
        super(RelabelWarning, self).__init__(line_number, line, position, node, old_label, new_label)
        self.node = node
        self.old_label = old_label
        self.new_label = new_label

    def __str__(self):
        return 'Tried to relabel {} from {} to {}'.format(self.node, self.old_label, self.new_label)
