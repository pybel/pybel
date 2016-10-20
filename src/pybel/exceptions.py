class PyBelError(Exception):
    """Raised when PyBEL can no longer continue"""


class PyBelWarning(Exception):
    """PyBEL throws exceptions labeled PyBEL1xx for statements that cannot be fixed automatically"""
    #:
    code = 0

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'PyBEL1{:02} - {}'.format(self.code, self.message)


class NamespaceMismatch(PyBelWarning):
    """Raised when the namespace name in a BEL document doesn't match
    the Namespace Keyword in the corresponding namespace file"""


class AnnotationMismatch(PyBelWarning):
    """Raised when the annotation name in a BEL document doesn't match
    the AnnotationDefinition Keyword in the corresponding annotation definition file"""
