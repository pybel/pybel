class PyBelError(Exception):
    """Raised when PyBEL can no longer continue"""


class NamespaceMismatch(PyBelError):
    """Raised when the namespace name in a BEL document doesn't match
    the Namespace Keyword in the corresponding namespace file"""


class AnnotationMismatch(PyBelError):
    """Raised when the annotation name in a BEL document doesn't match
    the AnnotationDefinition Keyword in the corresponding annotation definition file"""
