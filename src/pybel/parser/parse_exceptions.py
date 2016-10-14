class PyBelException(Exception):
    """PyBEL throws exceptions labeled PyBEL1xx for statements that cannot be fixed automatically"""
    #:
    code = 0

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'PyBEL1{:02} - {}'.format(self.code, self.message)


class IllegalAnnotationValueExeption(PyBelException):
    """Raised when an annotation has a value that does not belong to the original set of valid annotation values."""
    #:
    code = 1


class InvalidCitationException(PyBelException):
    """Raised when the format for a citation is wrong. It should have either {type, name, reference}; or {type, name, reference, date, authors, comments}"""
    #:
    code = 11


class NestedRelationNotSupportedException(PyBelException):
    """Raised when encountering a nested statement. See our wiki for an explanation of why we explicitly do not support nested statements."""
    #:
    code = 18


class IllegalNamespaceException(PyBelException):
    """Raised if reference made to undefined namespace"""
    #:
    code = 31


class IllegalNamespaceNameException(PyBelException):
    """Raised if reference to value not in namespace"""
    #:
    code = 32


class IllegalDefaultNameException(PyBelException):
    """Raised if reference to value not in default namespace"""
    #:
    code = 33


class PlaceholderAminoAcidException(PyBelException):
    """Raised for a placeholder amino acid (X)"""
    #:
    code = 15


class NakedNamespaceException(PyBelException):
    """Raised when there is an identifier without a namespace. Enable lenient mode to suppress"""
    #:
    code = 21


class IllegalTranslocationException(PyBelException):
    """Raised when there is a translocation statement without location information."""
    #:
    code = 8


class InvalidAnnotationKeyException(PyBelException):
    """Raised when an undefined annotation is used"""
    #:
    code = 20


class MissingAnnotationKeyException(PyBelException):
    """Raised when trying to unset an annotation that is not set"""
    #:
    code = 30
