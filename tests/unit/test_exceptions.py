"""Unit tests for custom exceptions."""

import pytest

from science_card_improvement.exceptions.custom_exceptions import (
    SciCardException,
    ConfigurationError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    RepositoryNotFoundError,
    CardGenerationError,
    PRSubmissionError,
    PortalIntegrationError,
    NetworkError,
    CacheError,
    ValidationError,
)


@pytest.mark.unit
class TestSciCardException:
    """Test base SciCardException class."""

    def test_basic_creation(self):
        """Test basic exception creation."""
        exc = SciCardException("Test error")
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.error_code == "SciCardException"
        assert exc.details == {}
        assert exc.retry_after is None

    def test_full_creation(self):
        """Test exception with all parameters."""
        exc = SciCardException(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"},
            retry_after=60
        )
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.details == {"key": "value"}
        assert exc.retry_after == 60

    def test_to_dict(self):
        """Test exception serialization."""
        exc = SciCardException(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"},
            retry_after=60
        )
        data = exc.to_dict()
        assert data["error"] == "TEST_ERROR"
        assert data["message"] == "Test error"
        assert data["details"] == {"key": "value"}
        assert data["retry_after"] == 60


@pytest.mark.unit
class TestConfigurationError:
    """Test ConfigurationError class."""

    def test_basic_creation(self):
        """Test basic configuration error."""
        exc = ConfigurationError("Missing config")
        assert exc.message == "Missing config"
        assert exc.error_code == "CONFIGURATION_ERROR"

    def test_with_config_key(self):
        """Test configuration error with config key."""
        exc = ConfigurationError("Missing config", config_key="API_KEY")
        assert exc.details["config_key"] == "API_KEY"


@pytest.mark.unit
class TestAuthenticationError:
    """Test AuthenticationError class."""

    def test_default_message(self):
        """Test default authentication error message."""
        exc = AuthenticationError()
        assert exc.message == "Authentication failed"
        assert exc.error_code == "AUTHENTICATION_ERROR"
        assert exc.details["service"] == "huggingface"

    def test_custom_message(self):
        """Test custom authentication error message."""
        exc = AuthenticationError("Invalid token", service="github")
        assert exc.message == "Invalid token"
        assert exc.details["service"] == "github"


@pytest.mark.unit
class TestAuthorizationError:
    """Test AuthorizationError class."""

    def test_default_message(self):
        """Test default authorization error message."""
        exc = AuthorizationError()
        assert exc.message == "Operation not authorized"
        assert exc.error_code == "AUTHORIZATION_ERROR"

    def test_with_resource_and_action(self):
        """Test authorization error with resource and action."""
        exc = AuthorizationError(
            "Cannot access",
            resource="dataset",
            action="write"
        )
        assert exc.details["resource"] == "dataset"
        assert exc.details["action"] == "write"


@pytest.mark.unit
class TestRateLimitError:
    """Test RateLimitError class."""

    def test_basic_creation(self):
        """Test basic rate limit error."""
        exc = RateLimitError("Too many requests")
        assert exc.message == "Too many requests"
        assert exc.error_code == "RATE_LIMIT_ERROR"

    def test_with_retry_after(self):
        """Test rate limit error with retry_after."""
        exc = RateLimitError("Too many requests", retry_after=60)
        assert exc.retry_after == 60

    def test_with_limit_info(self):
        """Test rate limit error with limit info."""
        exc = RateLimitError(
            "Too many requests",
            retry_after=60,
            limit=100,
            remaining=0
        )
        assert exc.details["limit"] == 100
        assert exc.details["remaining"] == 0


@pytest.mark.unit
class TestRepositoryNotFoundError:
    """Test RepositoryNotFoundError class."""

    def test_basic_creation(self):
        """Test basic repository not found error."""
        exc = RepositoryNotFoundError("user/dataset")
        assert "user/dataset" in exc.message
        assert exc.error_code == "REPOSITORY_NOT_FOUND"
        assert exc.details["repo_id"] == "user/dataset"

    def test_with_repo_type(self):
        """Test repository not found error with repo type."""
        exc = RepositoryNotFoundError("user/dataset", repo_type="model")
        assert exc.details["repo_type"] == "model"


@pytest.mark.unit
class TestCardGenerationError:
    """Test CardGenerationError class."""

    def test_basic_creation(self):
        """Test basic card generation error."""
        exc = CardGenerationError("Generation failed", repo_id="user/dataset")
        assert exc.message == "Generation failed"
        assert exc.error_code == "CARD_GENERATION_ERROR"
        assert exc.details["repo_id"] == "user/dataset"

    def test_with_reason(self):
        """Test card generation error with reason."""
        exc = CardGenerationError(
            "Generation failed",
            repo_id="user/dataset",
            reason="Invalid template"
        )
        assert exc.details["reason"] == "Invalid template"


@pytest.mark.unit
class TestPRSubmissionError:
    """Test PRSubmissionError class."""

    def test_basic_creation(self):
        """Test basic submission error."""
        exc = PRSubmissionError("Submission failed", repo_id="user/dataset")
        assert exc.message == "Submission failed"
        assert exc.error_code == "PR_SUBMISSION_ERROR"
        assert exc.details["repo_id"] == "user/dataset"

    def test_with_pr_url(self):
        """Test submission error with PR URL."""
        exc = PRSubmissionError(
            "Submission failed",
            repo_id="user/dataset",
            pr_url="https://github.com/user/dataset/pull/1"
        )
        assert "pr_url" in exc.details


@pytest.mark.unit
class TestPortalIntegrationError:
    """Test PortalIntegrationError class."""

    def test_basic_creation(self):
        """Test basic portal integration error."""
        exc = PortalIntegrationError("Portal error", portal="huggingface")
        assert exc.message == "Portal error"
        assert exc.error_code == "PORTAL_INTEGRATION_ERROR"
        assert exc.details["portal"] == "huggingface"


@pytest.mark.unit
class TestNetworkError:
    """Test NetworkError class."""

    def test_basic_creation(self):
        """Test basic network error."""
        exc = NetworkError("Connection failed")
        assert exc.message == "Connection failed"
        assert exc.error_code == "NETWORK_ERROR"

    def test_with_url_and_status(self):
        """Test network error with URL and status code."""
        exc = NetworkError(
            "Request failed",
            url="https://api.example.com",
            status_code=500
        )
        assert exc.details["url"] == "https://api.example.com"
        assert exc.details["status_code"] == 500


@pytest.mark.unit
class TestCacheError:
    """Test CacheError class."""

    def test_basic_creation(self):
        """Test basic cache error."""
        exc = CacheError("Cache miss")
        assert exc.message == "Cache miss"
        assert exc.error_code == "CACHE_ERROR"

    def test_with_cache_key(self):
        """Test cache error with cache key."""
        exc = CacheError("Cache miss", cache_key="user:123")
        assert exc.details["cache_key"] == "user:123"


@pytest.mark.unit
class TestValidationError:
    """Test ValidationError class."""

    def test_basic_creation(self):
        """Test basic validation error."""
        exc = ValidationError("Invalid value", field="email", value="not-an-email")
        assert exc.message == "Invalid value"
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.details["field"] == "email"
        assert exc.details["value"] == "not-an-email"
