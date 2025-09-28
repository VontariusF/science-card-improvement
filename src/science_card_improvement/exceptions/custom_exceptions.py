"""Custom exceptions for the Science Card Improvement toolkit."""

from typing import Any, Dict, Optional


class SciCardException(Exception):
    """Base exception for all Science Card Improvement exceptions."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ):
        """Initialize the exception.

        Args:
            message: Error message
            error_code: Optional error code for categorization
            details: Optional dictionary with additional error details
            retry_after: Optional seconds to wait before retrying
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.retry_after = retry_after

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
            "retry_after": self.retry_after,
        }


class ConfigurationError(SciCardException):
    """Raised when there's a configuration issue."""

    def __init__(self, message: str, config_key: Optional[str] = None):
        """Initialize configuration error."""
        details = {"config_key": config_key} if config_key else {}
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
        )


class AuthenticationError(SciCardException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", service: str = "huggingface"):
        """Initialize authentication error."""
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details={"service": service},
        )


class AuthorizationError(SciCardException):
    """Raised when an operation is not authorized."""

    def __init__(
        self,
        message: str = "Operation not authorized",
        resource: Optional[str] = None,
        action: Optional[str] = None,
    ):
        """Initialize authorization error."""
        details = {}
        if resource:
            details["resource"] = resource
        if action:
            details["action"] = action

        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details,
        )


class RateLimitError(SciCardException):
    """Raised when API rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 60,
        limit: Optional[int] = None,
        remaining: Optional[int] = None,
    ):
        """Initialize rate limit error."""
        details = {}
        if limit is not None:
            details["limit"] = limit
        if remaining is not None:
            details["remaining"] = remaining

        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details=details,
            retry_after=retry_after,
        )


class RepositoryNotFoundError(SciCardException):
    """Raised when a repository is not found."""

    def __init__(self, repo_id: str, repo_type: str = "dataset"):
        """Initialize repository not found error."""
        super().__init__(
            message=f"{repo_type.capitalize()} '{repo_id}' not found",
            error_code="REPOSITORY_NOT_FOUND",
            details={"repo_id": repo_id, "repo_type": repo_type},
        )


class CardValidationError(SciCardException):
    """Raised when card validation fails."""

    def __init__(self, message: str, validation_errors: Dict[str, Any]):
        """Initialize card validation error."""
        super().__init__(
            message=message,
            error_code="CARD_VALIDATION_ERROR",
            details={"validation_errors": validation_errors},
        )


class CardGenerationError(SciCardException):
    """Raised when card generation fails."""

    def __init__(self, message: str, repo_id: str, reason: Optional[str] = None):
        """Initialize card generation error."""
        details = {"repo_id": repo_id}
        if reason:
            details["reason"] = reason

        super().__init__(
            message=message,
            error_code="CARD_GENERATION_ERROR",
            details=details,
        )


class PRSubmissionError(SciCardException):
    """Raised when PR submission fails."""

    def __init__(self, message: str, repo_id: str, pr_url: Optional[str] = None):
        """Initialize PR submission error."""
        details = {"repo_id": repo_id}
        if pr_url:
            details["pr_url"] = pr_url

        super().__init__(
            message=message,
            error_code="PR_SUBMISSION_ERROR",
            details=details,
        )


class PortalIntegrationError(SciCardException):
    """Raised when portal integration operations fail."""

    def __init__(
        self,
        message: str,
        portal: str,
        operation: Optional[str] = None,
    ):
        """Initialize portal integration error."""
        details = {"portal": portal}
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            error_code="PORTAL_INTEGRATION_ERROR",
            details=details,
        )


class NetworkError(SciCardException):
    """Raised when network operations fail."""

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
    ):
        """Initialize network error."""
        details = {}
        if url:
            details["url"] = url
        if status_code:
            details["status_code"] = status_code

        super().__init__(
            message=message,
            error_code="NETWORK_ERROR",
            details=details,
        )


class CacheError(SciCardException):
    """Raised when cache operations fail."""

    def __init__(self, message: str, cache_key: Optional[str] = None):
        """Initialize cache error."""
        details = {"cache_key": cache_key} if cache_key else {}
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            details=details,
        )


class ValidationError(SciCardException):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str, value: Any):
        """Initialize validation error."""
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field": field, "value": str(value)},
        )


class ProcessingError(SciCardException):
    """Raised when data processing fails."""

    def __init__(self, message: str, step: str, data: Optional[Any] = None):
        """Initialize processing error."""
        details = {"step": step}
        if data:
            details["data_sample"] = str(data)[:100]  # Truncate for logging

        super().__init__(
            message=message,
            error_code="PROCESSING_ERROR",
            details=details,
        )


class TimeoutError(SciCardException):
    """Raised when an operation times out."""

    def __init__(self, message: str, operation: str, timeout: int):
        """Initialize timeout error."""
        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            details={"operation": operation, "timeout": timeout},
        )