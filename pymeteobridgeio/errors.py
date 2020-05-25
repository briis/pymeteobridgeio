"""Define package errors."""


class MeteoBridgeError(Exception):
    """Define a base error."""

    pass


class InvalidCredentials(MeteoBridgeError):
    """Define an error related to invalid or missing Credentials."""

    pass


class RequestError(MeteoBridgeError):
    """Define an error related to invalid requests."""

    pass

class ResultError(MeteoBridgeError):
    """Define an error related to the result returned from a request."""

    pass
