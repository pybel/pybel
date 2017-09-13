# -*- coding: utf-8 -*-

"""This module contains base exceptions that are shared through the package"""


class PyBelWarning(Exception):
    """The base class for warnings during compilation from which PyBEL can recover"""


class ResourceError(ValueError):
    """Base class for resource errors"""

    def __init__(self, location):
        super(ValueError, self).__init__(location)
        self.location = location


class EmptyResourceError(ResourceError):
    """Raised when downloading an empty file"""

    def __str__(self):
        return 'Downloaded empty resource at {}'.format(self.location)


class MissingSectionError(ResourceError):
    """Raised when downloading a resource without a [Values] Section"""

    def __str__(self):
        return 'No [Values] section found in {}'.format(self.location)
