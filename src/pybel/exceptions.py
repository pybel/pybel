"""This module contains base exceptions that are shared through the package.

A message for "General Parser Failure" is displayed when a problem was caused due to an unforeseen error. The line
number and original statement are printed for the user to debug.
"""

from .utils import ensure_quotes


class PyBELWarning(Exception):
    """The base class for warnings during compilation from which PyBEL can recover."""


class BELParserWarning(PyBELWarning):
    """The base PyBEL parser exception, which holds the line and position where a parsing problem occurred."""

    def __init__(self, line_number: int, line: str, position: int, *args):
        """Initialize the BEL parser warning.

        :param line_number: The line number on which this warning occurred
        :param line: The content of the line
        :param position: The position within the line where the warning occurred
        """
        super().__init__(line_number, line, position, *args)
        self.line_number = line_number
        self.line = line
        self.position = position

    def __str__(self):
        return f"General Parser Failure on line {self.line_number} at pos {self.position}: {self.line}"


class BELSyntaxError(BELParserWarning, SyntaxError):
    """For general syntax errors."""


class InconsistentDefinitionError(BELParserWarning):
    """Base PyBEL error for redefinition."""

    def __init__(self, line_number: int, line: str, position: int, definition: str):
        super().__init__(line_number, line, position, definition)
        self.definition = definition

    def __str__(self):
        return f"Tried to redefine {self.definition} with: {self.line}"


class RedefinedNamespaceError(InconsistentDefinitionError):
    """Raised when a namespace is redefined."""


class RedefinedAnnotationError(InconsistentDefinitionError):
    """Raised when an annotation is redefined."""


# Naming Warnings


class NameWarning(BELParserWarning):
    """The base class for errors related to nomenclature."""

    def __init__(self, line_number: int, line: str, position: int, name: str, *args):
        """Build a warning wrapping a given name."""
        super().__init__(line_number, line, position, name, *args)
        self.name = name


class NakedNameWarning(NameWarning):
    """Raised when there is an identifier without a namespace. Enable lenient mode to suppress."""

    def __str__(self):
        return f'"{self.name}" should be qualified with a valid namespace'


class MissingDefaultNameWarning(NameWarning):
    """Raised if reference to value not in default namespace."""

    def __str__(self):
        return f'"{self.name}" is not in the default namespace'


class NamespaceIdentifierWarning(NameWarning):
    """The base class for warnings related to namespace:name identifiers."""

    def __init__(self, line_number: int, line: str, position: int, namespace: str, name: str):
        """Initialize the namespace identifier warning.

        :param line_number: The line number of the line that caused the exception
        :param line: The line that caused the exception
        :param position: The line's position of the exception
        :param namespace: The namespace of the identifier
        :param name: The name of the identifier
        """
        super().__init__(line_number, line, position, name, namespace)
        self.namespace = namespace


class UndefinedNamespaceWarning(NamespaceIdentifierWarning):
    """Raised if reference made to undefined namespace."""

    def __str__(self):
        return f'"{self.namespace}" is not a defined namespace'


class MissingNamespaceNameWarning(NamespaceIdentifierWarning):
    """Raised if reference to value not in namespace."""

    def __str__(self):
        return f'"{self.name}" is not in the {self.namespace} namespace'


class MissingNamespaceRegexWarning(NamespaceIdentifierWarning):
    """Raised if reference not matching regex."""

    def __str__(self):
        return f""""{self.name}" doesn't match the regex for {self.namespace} namespace"""


class AnnotationWarning(BELParserWarning):
    """Base exception for annotation warnings."""

    def __init__(self, line_number, line, position, annotation, *args):
        """Build an AnnotationWarning.

        :param int line_number: The line number on which the warning occurred
        :param str line: The line on which the warning occurred
        :param int position: The position in the line that caused the warning
        :param str annotation: The annotation name that caused the warning
        """
        super().__init__(line_number, line, position, annotation, *args)
        self.annotation = annotation


class UndefinedAnnotationWarning(AnnotationWarning):
    """Raised when an undefined annotation is used."""

    def __str__(self):
        return f""""{self.annotation}" is not defined"""


class MissingAnnotationKeyWarning(AnnotationWarning):
    """Raised when trying to unset an annotation that is not set."""

    def __str__(self):
        return f""""{self.annotation}" is not set, so it can't be unset"""


class AnnotationIdentifierWarning(AnnotationWarning):
    """Base exception for annotation:value pairs."""

    def __init__(self, line_number, line, position, annotation, value):
        super().__init__(line_number, line, position, annotation, value)
        self.value = value


class IllegalAnnotationValueWarning(AnnotationIdentifierWarning):
    """Raised when an annotation has a value that does not belong to the original set of valid annotation values."""

    def __str__(self):
        return f'"{self.value}" is not defined in the {self.annotation} annotation'


class MissingAnnotationRegexWarning(AnnotationIdentifierWarning):
    """Raised if annotation doesn't match regex."""

    def __str__(self):
        return f""""{self.value}" doesn't match the regex for {self.annotation} annotation"""


# Provenance Warnings


class VersionFormatWarning(BELParserWarning):
    """Raised if the version string doesn't adhere to semantic versioning or ``YYYYMMDD`` format."""

    def __init__(self, line_number, line, position, version_string):
        super().__init__(line_number, line, position, version_string)
        self.version_string = version_string

    def __str__(self):
        return (
            f'Version string "{self.version_string}" neither is a date like YYYYMMDD nor adheres to semantic versioning.'
            " See http://semver.org/"
        )


class MetadataException(BELParserWarning):
    """Base exception for issues with document metadata."""

    def __str__(self):
        return f'Invalid metadata - "{self.line}"'


class MalformedMetadataException(MetadataException):
    """Raised when an invalid metadata line is encountered."""


class InvalidMetadataException(BELParserWarning):
    """Raised when an incorrect document metadata key is used.

    .. hint:: Valid document metadata keys are:

        - ``Authors``
        - ``ContactInfo``
        - ``Copyright``
        - ``Description``
        - ``Disclaimer``
        - ``Licenses``
        - ``Name``
        - ``Version``

    .. seealso:: BEL specification on the `properties section <http://openbel.org/language/web/version_1.0/
                 bel_specification_version_1.0.html#_properties_section>`_
    """

    def __init__(self, line_number, line, position, key, value):
        super().__init__(line_number, line, position, key, value)
        self.key = key
        self.value = value

    def __str__(self):
        return f"Invalid document metadata key: {self.key}"


class MissingMetadataException(BELParserWarning):
    """Raised when a BEL Script is missing critical metadata."""

    def __init__(self, line_number, line, position, key):
        super().__init__(line_number, line, position, key)
        self.key = key

    def __str__(self):
        return f"Missing required document metadata: {self.key}"

    @staticmethod
    def make(key: str):
        """Build an instance of this class with auto-filled dummy values.

        Unlike normal classes, polymorphism on __init__ can't be used for exceptions when pickling/unpickling.
        """
        return MissingMetadataException(0, "", 0, key)


class InvalidCitationLengthException(BELParserWarning):
    """Base exception raised when the format for a citation is wrong."""


class CitationTooShortException(InvalidCitationLengthException):
    """Raised when a citation does not have the minimum of {type, name, reference}."""

    def __str__(self):
        return f"Citation is missing required fields: {self.line}"


class CitationTooLongException(InvalidCitationLengthException):
    """Raised when a citation has more than the allowed entries, {type, name, reference, date, authors, comments}."""

    def __str__(self):
        return f"Citation contains too many entries: {self.line}"


class MissingCitationException(BELParserWarning):
    """Raised when trying to parse a BEL statement, but no citation is currently set.

    This might be due to a previous error in the formatting of a citation.

    Though it's not a best practice, some BEL curators set other annotations before the citation. If this is the case
    in your BEL document, and you're *absolutely* sure that all ``UNSET`` statements are correctly written, you can use
    ``citation_clearing=True`` as a keyword argument in any of the IO functions in :func:`pybel.from_lines`,
    :func:`pybel.from_url`, or :func:`pybel.from_path`.
    """

    def __str__(self):
        return f"Missing citation; can't add: {self.line}"


class MissingSupportWarning(BELParserWarning):
    """Raised when trying to parse a BEL statement, but no evidence is currently set.

    All BEL statements must be qualified with evidence.

    If your data is serialized from a database and provenance information is not readily
    accessible, consider referencing the publication for the database, or a url pointing to the data from either
    a programmatically or human-readable endpoint.
    """

    def __str__(self):
        return f"Missing evidence; can't add: {self.line}"


class MissingAnnotationWarning(BELParserWarning):
    """Raised when trying to parse a BEL statement and a required annotation is not present."""

    def __init__(self, line_number, line, position, required_annotations):
        super().__init__(line_number, line, position, required_annotations)
        self.required_annotations = required_annotations

    def __str__(self):
        return "Missing annotations: {}".format(", ".join(sorted(self.required_annotations)))


class InvalidCitationType(BELParserWarning):
    """Raised when a citation is set with an incorrect type.

    .. hint:: Valid citation types include:

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
        super().__init__(line_number, line, position, citation_type)
        self.citation_type = citation_type

    def __str__(self):
        return f'"{self.citation_type}" is not a valid citation type'


class InvalidPubMedIdentifierWarning(BELParserWarning):
    """Raised when a citation is set whose type is ``PubMed`` but whose database identifier is not a valid integer."""

    def __init__(self, line_number, line, position, reference):
        super().__init__(line_number, line, position, reference)
        self.reference = reference

    def __str__(self):
        return f'"{self.reference}" is not a valid PubMed identifier'


# BEL Syntax Warnings


class MalformedTranslocationWarning(BELParserWarning):
    """Raised when there is a translocation statement without location information."""

    def __init__(self, line_number, line, position, tokens):
        super().__init__(line_number, line, position, tokens)
        self.tokens = tokens

    def __str__(self):
        return f"Unqualified translocation: {self.line} {self.tokens}"


class PlaceholderAminoAcidWarning(BELParserWarning):
    """Raised when an invalid amino acid code is given.

    One example might be the usage of X, which is a colloquial signifier for a truncation in a given position. Text
    mining efforts for knowledge extraction make this mistake often. X might also signify a placeholder amino acid.
    """

    def __init__(self, line_number, line, position, code):
        super().__init__(line_number, line, position, code)
        self.code = code

    def __str__(self):
        return f"Placeholder amino acid found: {self.code}"


class NestedRelationWarning(BELParserWarning):
    """Raised when encountering a nested statement.

    See our the docs for an explanation of why we explicitly do not support nested statements.
    """

    def __str__(self):
        return f"Nesting is not supported. Split this statement: {self.line}"


# Semantic Warnings


class InvalidEntity(BELParserWarning):
    """Raised when using a non-entity name for a name."""

    def __init__(self, line_number, line, position, namespace, name):
        super().__init__(line_number, line, position, namespace, name)
        self.namespace = namespace
        self.name = name

    def __str__(self):
        return f"{self.namespace}:{ensure_quotes(self.name)} should not be coded as an entity"


class InvalidFunctionSemantic(BELParserWarning):
    """Raised when an invalid function is used for a given node.

    For example, an HGNC symbol for a protein-coding gene YFG cannot be referenced as an miRNA with ``m(HGNC:YFG)``
    """

    def __init__(self, line_number, line, position, func, namespace, name, allowed_functions):
        super().__init__(line_number, line, position, func, namespace, name, allowed_functions)
        self.func = func
        self.namespace = namespace
        self.name = name
        self.allowed_functions = allowed_functions

    def __str__(self):
        return "{} {}:{} should be encoded as one of: {}".format(
            self.func,
            self.namespace,
            ensure_quotes(self.name),
            ", ".join(self.allowed_functions),
        )
