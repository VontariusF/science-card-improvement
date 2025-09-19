"""Application configuration and settings management."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Science Card Improvement"
    app_version: str = "1.0.0"
    debug: bool = Field(False)
    environment: str = Field("production")

    # Hugging Face
    hf_token: Optional[SecretStr] = Field(None)
    hf_endpoint: str = Field("https://huggingface.co")
    hf_api_timeout: int = Field(30)
    hf_max_retries: int = Field(3)

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    config_dir: Optional[Path] = None
    templates_dir: Optional[Path] = None
    cache_dir: Optional[Path] = None
    logs_dir: Optional[Path] = None
    output_dir: Optional[Path] = None

    # Discovery settings
    discovery_batch_size: int = Field(100)
    discovery_max_workers: int = Field(10)
    discovery_cache_ttl: int = Field(3600)

    # Assessment settings
    assessment_min_readme_length: int = Field(300)
    assessment_required_sections: List[str] = Field(
        default_factory=lambda: [
            "description",
            "dataset_structure",
            "license",
            "citation",
        ]
    )

    # Generation settings
    generation_model: str = Field("gpt-4")
    generation_temperature: float = Field(0.7)
    generation_max_tokens: int = Field(4000)

    # Submission settings
    submission_branch_prefix: str = Field("improve-card")
    submission_pr_template: str = Field("pr_template.md")
    submission_dry_run: bool = Field(False)

    # Monitoring
    monitoring_enabled: bool = Field(True)
    monitoring_port: int = Field(8080)
    monitoring_metrics_path: str = Field("/metrics")

    # Logging
    log_level: str = Field("INFO")
    log_format: str = Field("json")
    log_file_enabled: bool = Field(True)
    log_file_rotation: str = Field("1 day")
    log_file_retention: str = Field("30 days")

    # Database (for future scalability)
    database_url: Optional[str] = Field(None)
    database_pool_size: int = Field(10)
    database_max_overflow: int = Field(20)

    # Redis cache (for future scalability)
    redis_url: Optional[str] = Field(None)
    redis_ttl: int = Field(3600)

    # API rate limiting
    rate_limit_enabled: bool = Field(True)
    rate_limit_requests: int = Field(100)
    rate_limit_window: int = Field(60)

    # Feature flags
    feature_auto_tagging: bool = Field(True)
    feature_quality_scoring: bool = Field(True)
    feature_ai_generation: bool = Field(False)
    feature_batch_processing: bool = Field(True)

    @model_validator(mode="after")
    def _set_directories(self) -> "Settings":
        """Populate directory attributes if they were not provided."""

        directory_map = {
            "config_dir": "config",
            "templates_dir": "templates",
            "cache_dir": ".cache",
            "logs_dir": "logs",
            "output_dir": "output",
        }
        for attr, default_name in directory_map.items():
            if getattr(self, attr) is None:
                setattr(self, attr, self.base_dir / default_name)
        return self

    @field_validator("hf_token")
    def validate_hf_token(cls, value: Optional[SecretStr]) -> Optional[SecretStr]:
        """Validate Hugging Face token if provided."""

        if value and len(value.get_secret_value()) < 10:
            raise ValueError("Invalid Hugging Face token format")
        return value

    def create_directories(self) -> None:
        """Create necessary directories if they don't exist."""

        for dir_path in (self.cache_dir, self.logs_dir, self.output_dir):
            if dir_path is not None:
                dir_path.mkdir(parents=True, exist_ok=True)

    def get_hf_headers(self) -> Dict[str, str]:
        """Get headers for Hugging Face API requests."""

        headers = {"User-Agent": f"{self.app_name}/{self.app_version}"}
        if self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token.get_secret_value()}"
        return headers

    def to_dict(self, *, exclude_secrets: bool = True) -> Dict[str, Any]:
        """Convert settings to dictionary."""

        data = self.model_dump()
        if exclude_secrets:
            data.pop("hf_token", None)
            data.pop("database_url", None)
            data.pop("redis_url", None)
        return data


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings singleton."""

    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.create_directories()
    return _settings


def reset_settings() -> None:
    """Reset settings singleton (useful for testing)."""

    global _settings
    _settings = None
