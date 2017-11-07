# -*- coding: utf-8 -*-


class ResourceError(ValueError):
    """Base class for resource errors"""

    def __init__(self, location):
        super(ValueError, self).__init__(location)
        self.location = location


class EmptyResourceError(ResourceError):
    """Raised when downloading an empty file"""

    def __str__(self):
        return 'Downloaded empty resource at {}'.format(self.location)
