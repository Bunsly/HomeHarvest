class InvalidSite(Exception):
    """Raised when a provided site is does not exist."""


class InvalidListingType(Exception):
    """Raised when a provided listing type is does not exist."""


class NoResultsFound(Exception):
    """Raised when no results are found for the given location"""


class PropertyNotFound(Exception):
    """Raised when no property is found for the given address"""
