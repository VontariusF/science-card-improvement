"""Input validation for API requests and data processing."""

import re
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, validator, HttpUrl

from src.exceptions.custom_exceptions import ValidationError


class RepositoryIdValidator(BaseModel):
    """Validator for Hugging Face repository IDs."""

    repo_id: str = Field(..., description="Repository ID in format 'owner/name'")
    repo_type: str = Field("dataset", description="Repository type")

    @validator("repo_id")
    def validate_repo_id(cls, v: str) -> str:
        """Validate repository ID format."""
        if not v or not isinstance(v, str):
            raise ValueError("Repository ID must be a non-empty string")

        # Check format
        pattern = r"^[\w\-\.]+/[\w\-\.]+$"
        if not re.match(pattern, v):
            raise ValueError(
                "Invalid repository ID format. Must be 'owner/name' with alphanumeric, "
                "hyphen, underscore, or dot characters only"
            )

        # Check length
        if len(v) > 100:
            raise ValueError("Repository ID too long (max 100 characters)")

        return v

    @validator("repo_type")
    def validate_repo_type(cls, v: str) -> str:
        """Validate repository type."""
        allowed_types = ["dataset", "model", "space"]
        if v not in allowed_types:
            raise ValueError(f"Repository type must be one of: {', '.join(allowed_types)}")
        return v


class DiscoveryRequestValidator(BaseModel):
    """Validator for discovery API requests."""

    repo_type: str = Field("both", description="Repository type to discover")
    limit: int = Field(100, ge=1, le=1000, description="Maximum results")
    keywords: Optional[List[str]] = Field(None, max_items=50)
    sort_by: str = Field("priority", description="Sort criteria")
    filters: Optional[Dict[str, Any]] = Field(None)

    @validator("repo_type")
    def validate_repo_type(cls, v: str) -> str:
        """Validate repository type."""
        allowed_types = ["dataset", "model", "both"]
        if v not in allowed_types:
            raise ValueError(f"Repository type must be one of: {', '.join(allowed_types)}")
        return v

    @validator("keywords")
    def validate_keywords(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate keywords list."""
        if v is None:
            return v

        # Check each keyword
        for keyword in v:
            if not isinstance(keyword, str):
                raise ValueError("All keywords must be strings")
            if len(keyword) < 2:
                raise ValueError("Keywords must be at least 2 characters")
            if len(keyword) > 50:
                raise ValueError("Keywords must be at most 50 characters")

        return v

    @validator("sort_by")
    def validate_sort_by(cls, v: str) -> str:
        """Validate sort criteria."""
        allowed_sorts = ["downloads", "likes", "updated", "priority", "readme_quality"]
        if v not in allowed_sorts:
            raise ValueError(f"Sort criteria must be one of: {', '.join(allowed_sorts)}")
        return v

    @validator("filters")
    def validate_filters(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate filter parameters."""
        if v is None:
            return v

        allowed_filters = {
            "min_downloads": int,
            "min_likes": int,
            "max_readme_length": int,
            "has_readme": bool,
            "needs_improvement": bool,
        }

        for key, value in v.items():
            if key not in allowed_filters:
                raise ValueError(f"Unknown filter: {key}")

            expected_type = allowed_filters[key]
            if not isinstance(value, expected_type):
                raise ValueError(f"Filter '{key}' must be of type {expected_type.__name__}")

            # Validate ranges
            if key in ["min_downloads", "min_likes", "max_readme_length"]:
                if value < 0:
                    raise ValueError(f"Filter '{key}' must be non-negative")

        return v


class CardGenerationRequestValidator(BaseModel):
    """Validator for card generation requests."""

    repo_id: str = Field(..., description="Repository ID")
    repo_type: str = Field("dataset", description="Repository type")
    template: str = Field("comprehensive", description="Template to use")
    include_examples: bool = Field(True, description="Include usage examples")
    include_citation: bool = Field(True, description="Include citation")
    custom_fields: Optional[Dict[str, str]] = Field(None, description="Custom fields")

    @validator("repo_id")
    def validate_repo_id(cls, v: str) -> str:
        """Validate repository ID."""
        validator = RepositoryIdValidator(repo_id=v, repo_type="dataset")
        return validator.repo_id

    @validator("template")
    def validate_template(cls, v: str) -> str:
        """Validate template name."""
        allowed_templates = ["comprehensive", "minimal", "scientific", "medical", "custom"]
        if v not in allowed_templates:
            raise ValueError(f"Template must be one of: {', '.join(allowed_templates)}")
        return v

    @validator("custom_fields")
    def validate_custom_fields(cls, v: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """Validate custom fields."""
        if v is None:
            return v

        if len(v) > 20:
            raise ValueError("Maximum 20 custom fields allowed")

        for key, value in v.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("Custom field keys and values must be strings")
            if len(key) > 50:
                raise ValueError("Custom field keys must be at most 50 characters")
            if len(value) > 5000:
                raise ValueError("Custom field values must be at most 5000 characters")

        return v


class PRSubmissionValidator(BaseModel):
    """Validator for PR submission requests."""

    repo_id: str = Field(..., description="Repository ID")
    repo_type: str = Field("dataset", description="Repository type")
    card_content: str = Field(..., min_length=100, max_length=100000)
    pr_title: str = Field(..., min_length=5, max_length=200)
    pr_description: str = Field(..., min_length=10, max_length=5000)
    branch_name: Optional[str] = Field(None, max_length=100)
    commit_message: Optional[str] = Field(None, max_length=500)

    @validator("repo_id")
    def validate_repo_id(cls, v: str) -> str:
        """Validate repository ID."""
        validator = RepositoryIdValidator(repo_id=v, repo_type="dataset")
        return validator.repo_id

    @validator("branch_name")
    def validate_branch_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate branch name."""
        if v is None:
            return v

        # Check format
        pattern = r"^[\w\-\.\/]+$"
        if not re.match(pattern, v):
            raise ValueError("Invalid branch name format")

        return v


class TagSuggestionValidator(BaseModel):
    """Validator for tag suggestion requests."""

    repo_id: str = Field(..., description="Repository ID")
    repo_type: str = Field("dataset", description="Repository type")
    existing_tags: List[str] = Field(default_factory=list, max_items=100)
    max_suggestions: int = Field(10, ge=1, le=50)
    include_domain_tags: bool = Field(True)

    @validator("existing_tags")
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate tag list."""
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError("All tags must be strings")
            if len(tag) < 1 or len(tag) > 50:
                raise ValueError("Tags must be 1-50 characters")

        return v


class BatchProcessingValidator(BaseModel):
    """Validator for batch processing requests."""

    repo_ids: List[str] = Field(..., min_items=1, max_items=100)
    operation: str = Field(..., description="Operation to perform")
    parallel_workers: int = Field(5, ge=1, le=20)
    continue_on_error: bool = Field(True)
    dry_run: bool = Field(False)

    @validator("repo_ids")
    def validate_repo_ids(cls, v: List[str]) -> List[str]:
        """Validate repository IDs."""
        for repo_id in v:
            try:
                validator = RepositoryIdValidator(repo_id=repo_id, repo_type="dataset")
            except Exception as e:
                raise ValueError(f"Invalid repository ID '{repo_id}': {str(e)}")
        return v

    @validator("operation")
    def validate_operation(cls, v: str) -> str:
        """Validate operation."""
        allowed_operations = [
            "assess_quality",
            "generate_cards",
            "submit_prs",
            "suggest_tags",
            "export_metadata",
        ]
        if v not in allowed_operations:
            raise ValueError(f"Operation must be one of: {', '.join(allowed_operations)}")
        return v


class ConfigUpdateValidator(BaseModel):
    """Validator for configuration updates."""

    setting_key: str = Field(..., description="Setting key to update")
    setting_value: Any = Field(..., description="New value")
    persist: bool = Field(False, description="Persist to file")

    @validator("setting_key")
    def validate_setting_key(cls, v: str) -> str:
        """Validate setting key."""
        # List of allowed settings that can be updated
        allowed_settings = [
            "log_level",
            "discovery_batch_size",
            "discovery_max_workers",
            "assessment_min_readme_length",
            "generation_temperature",
            "submission_dry_run",
            "rate_limit_requests",
            "rate_limit_window",
        ]

        if v not in allowed_settings:
            raise ValueError(f"Setting '{v}' cannot be updated via API")

        return v


def validate_file_content(content: str, file_type: str = "markdown") -> bool:
    """Validate file content.

    Args:
        content: File content to validate
        file_type: Type of file (markdown, json, yaml)

    Returns:
        Validation status

    Raises:
        ValidationError: If content is invalid
    """
    if not content:
        raise ValidationError("Content cannot be empty", "content", content)

    # Check size
    max_size = 1024 * 1024  # 1MB
    if len(content) > max_size:
        raise ValidationError(
            f"Content too large (max {max_size} bytes)",
            "content",
            len(content)
        )

    if file_type == "markdown":
        # Basic markdown validation
        if not any(line.startswith("#") for line in content.split("\n")):
            raise ValidationError(
                "Markdown must contain at least one heading",
                "content",
                "no headings"
            )

    elif file_type == "json":
        # Validate JSON
        import json
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON: {str(e)}", "content", content[:100])

    elif file_type == "yaml":
        # Validate YAML
        import yaml
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML: {str(e)}", "content", content[:100])

    return True


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input.

    Args:
        text: Input text
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove control characters
    text = "".join(char for char in text if char.isprintable() or char in ["\n", "\t"])

    # Trim to max length
    text = text[:max_length]

    # Remove potentially dangerous patterns
    dangerous_patterns = [
        r"<script[^>]*>.*?</script>",  # Script tags
        r"javascript:",  # JavaScript protocol
        r"on\w+\s*=",  # Event handlers
    ]

    for pattern in dangerous_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    return text.strip()


class URLValidator:
    """URL validation utilities."""

    @staticmethod
    def validate_huggingface_url(url: str) -> bool:
        """Validate Hugging Face URL.

        Args:
            url: URL to validate

        Returns:
            Validation status
        """
        pattern = r"^https?://huggingface\.co/(datasets|models|spaces)/[\w\-\.]+/[\w\-\.]+/?.*$"
        return bool(re.match(pattern, url))

    @staticmethod
    def extract_repo_from_url(url: str) -> Tuple[str, str]:
        """Extract repository ID and type from URL.

        Args:
            url: Hugging Face URL

        Returns:
            Tuple of (repo_id, repo_type)

        Raises:
            ValidationError: If URL is invalid
        """
        if not URLValidator.validate_huggingface_url(url):
            raise ValidationError("Invalid Hugging Face URL", "url", url)

        # Extract components
        match = re.match(
            r"^https?://huggingface\.co/(datasets|models|spaces)/([\w\-\.]+/[\w\-\.]+)",
            url
        )

        if not match:
            raise ValidationError("Could not parse repository from URL", "url", url)

        repo_type = match.group(1).rstrip("s")  # Remove trailing 's'
        repo_id = match.group(2)

        return repo_id, repo_type