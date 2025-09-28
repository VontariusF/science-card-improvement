"""Custom exceptions for science card improvement."""

from .custom_exceptions import (
    AuthenticationError,
    AuthorizationError,
    CacheError,
    ConfigurationError,
    NetworkError,
    PortalIntegrationError,
    RateLimitError,
    RepositoryNotFoundError,
    ValidationError,
)

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "CacheError",
    "ConfigurationError",
    "NetworkError",
    "PortalIntegrationError",
    "RateLimitError",
    "RepositoryNotFoundError",
    "ValidationError",
]
