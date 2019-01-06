# -*- coding: utf-8 -*-

"""Exceptions for downloading, reading, and writing BEL script, namespace files, and annotation files."""


class ResourceError(ValueError):
    """A base class for resource errors."""

    def __init__(self, location: str):  # noqa: D107
        """Initialize the ResourceError.

        :param location: The URL location of the BEL resource
        """
        super().__init__(location)

    @property
    def location(self):  # noqa: D401
        """The URL location of the BEL resource."""
        return self.args[0]


class MissingResourceError(ResourceError):
    """Raised when trying to download a file that doesn't exist anymore."""

    def __str__(self):
        return "Can't locate resource: {}".format(self.location)


class InvalidResourceError(ResourceError):
    """Raised when downloading a file that is not actually a BEL resource file."""

    def __str__(self):
        return 'URL does not point to a BEL resource: {}'.format(self.location)


class EmptyResourceError(ResourceError):
    """Raised when downloading an empty file."""

    def __str__(self):
        return 'Downloaded empty resource at {}'.format(self.location)
