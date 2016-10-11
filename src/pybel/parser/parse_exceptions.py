class PyBelException(Exception):
    pass


class IllegalAnnotationValueExeption(PyBelException):
    pass


class InvalidCitationException(PyBelException):
    pass


class NestedRelationNotSupportedException(PyBelException):
    pass


class NamespaceException(PyBelException):
    pass


class PlaceholderAminoAcidException(PyBelException):
    pass


class NakedNamespaceException(PyBelException):
    pass
