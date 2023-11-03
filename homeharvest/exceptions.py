class InvalidListingType(Exception):
    """Raised when a provided listing type is does not exist."""

class InvalidDate(Exception):
    """Raised when only one of date_from or date_to is provided or not in the correct format. ex: 2023-10-23 """
