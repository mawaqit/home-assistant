class Error(Exception):
    """Base class for exceptions in this module."""

    pass


class CalculationMethodError(Error):
    """Exception raised for invalid calculation method"""

    pass


class InvalidResponseError(Error):
    """Exception raised when receiving an invalid response"""

    pass