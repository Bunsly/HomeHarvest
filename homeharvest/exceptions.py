class InvalidListingType(Exception):
    """Raised when a provided listing type is does not exist."""


class NoResultsFound(Exception):
    """Raised when no results are found for the given location"""
