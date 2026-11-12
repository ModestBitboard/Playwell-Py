class PlaywellError(Exception):
    """Base exception for all errors raised by the Playwell client SDK."""
    pass

class PlaywellConnectionError(PlaywellError):
    """Raised when the Playwell server cannot be reached or times out."""
    pass

class PlaywellVersionError(PlaywellError):
    """Raised when the connected server does not support the client's API version."""
    pass


class PlaywellAPIError(PlaywellError):
    """Raised when the server returns an unexpected 4xx or 5xx HTTP status code."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")

class PlaywellNotFoundError(PlaywellAPIError):
    """Raised when a requested kit ID or instruction manual does not exist (HTTP 404)."""
    def __init__(self, message: str = "The requested resource was not found."):
        super().__init__(status_code=404, message=message)
