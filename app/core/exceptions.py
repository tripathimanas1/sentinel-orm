"""Custom exceptions for the application."""

from typing import Any, Optional


class SentinelORMException(Exception):
    """Base exception for Sentinel ORM."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(SentinelORMException):
    """Database-related exceptions."""
    pass


class ModelException(SentinelORMException):
    """ML model-related exceptions."""
    pass


class IngestionException(SentinelORMException):
    """Signal ingestion exceptions."""
    pass


class ValidationException(SentinelORMException):
    """Data validation exceptions."""
    pass


class AuthenticationException(SentinelORMException):
    """Authentication exceptions."""
    pass


class AuthorizationException(SentinelORMException):
    """Authorization exceptions."""
    pass


class NotFoundException(SentinelORMException):
    """Resource not found exceptions."""
    pass


class RateLimitException(SentinelORMException):
    """Rate limiting exceptions."""
    pass
