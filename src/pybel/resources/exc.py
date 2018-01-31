# -*- coding: utf-8 -*-


class ResourceError(ValueError):
    """Base class for resource errors"""

    def __init__(self, location):
        super(ValueError, self).__init__(location)
        self.location = location


class MissingResourceError(ResourceError):
    """Raised when trying to download a file that doesn't exist anymore"""

    def __str__(self):
        return "Can't locate resource: {}".format(self.location)


class InvalidResourceError(ResourceError):
    """Raise when downloading a file that is not actually a BEL resource file"""

    def __str__(self):
        return 'URL does not point to a BEL resource: {}'.format(self.location)


class EmptyResourceError(ResourceError):
    """Raised when downloading an empty file"""

    def __str__(self):
        return 'Downloaded empty resource at {}'.format(self.location)
