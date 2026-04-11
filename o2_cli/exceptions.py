"""Custom exception hierarchy for O2 CLI."""


class O2CLIError(Exception):
    """Base exception for O2 CLI."""
    pass


class AuthenticationError(O2CLIError):
    """Auth failure (no token, expired, invalid)."""
    pass


class APIError(O2CLIError):
    """Backend returned non-success response."""

    def __init__(self, status_code: int, detail: str, code: str | None = None):
        self.status_code = status_code
        self.detail = detail
        self.code = code
        super().__init__(f"[{status_code}] {detail}" + (f" (code={code})" if code else ""))


class ConfigError(O2CLIError):
    """Configuration file error."""
    pass


class ConnectionError(O2CLIError):
    """Cannot reach backend."""
    pass
