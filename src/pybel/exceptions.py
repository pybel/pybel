class PyBelEpicFailure(Exception):
    pass


class NamespaceMismatch(PyBelEpicFailure):
    """Raised when the namespace name in a BEL document doesn't match
    the Namespace Keyword in the corresponding namespace file"""


class AnnotationMismatch(PyBelEpicFailure):
    """Raised when the annotation name in a BEL document doesn't match
    the AnnotationDefinition Keyword in the corresponding annotation definition file"""
