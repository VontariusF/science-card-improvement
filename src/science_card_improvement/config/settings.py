"""Application configuration and settings management."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
    )

    # Application
    app_name: str = "Science Card Improvement"
    app_version: str = "1.0.0"
    debug: bool = Field(False, validation_alias=AliasChoices("API_DEBUG", "DEBUG", "debug"))
    environment: str = Field("production")
    project_name: str = Field("science-card-improvement", alias="PROJECT_NAME")

    # Hugging Face
    hf_token: Optional[SecretStr] = Field(None)
    huggingface_api_token: Optional[SecretStr] = Field(None, alias="HUGGINGFACE_API_TOKEN")
    hf_endpoint: str = Field("https://huggingface.co")
    hf_api_timeout: int = Field(30)
    hf_max_retries: int = Field(3)
    hf_hub_cache: Optional[str] = Field(None, alias="HF_HUB_CACHE")
    hf_datasets_cache: Optional[str] = Field(None, alias="HF_DATASETS_CACHE")

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent.parent.parent
    config_dir: Optional[Path] = Field(None, alias="CONFIG_DIR")
    templates_dir: Optional[Path] = Field(None, alias="TEMPLATES_DIR")
    cache_dir: Optional[Path] = Field(None)
    logs_dir: Optional[Path] = Field(None)
    output_dir: Optional[Path] = Field(None)

    # Discovery settings
    discovery_batch_size: int = Field(100)
    discovery_max_workers: int = Field(10)
    discovery_cache_ttl: int = Field(3600, alias="CACHE_TTL")

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
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_format: str = Field("json")
    log_file_enabled: bool = Field(True)
    log_file_rotation: str = Field("1 day")
    log_file_retention: str = Field("30 days")

    # Database (for future scalability)
    database_url: Optional[str] = Field(None, alias="DATABASE_URL")
    database_pool_size: int = Field(10)
    database_max_overflow: int = Field(20)

    # Redis cache (for future scalability)
    redis_url: Optional[str] = Field(None)
    redis_ttl: int = Field(3600)

    # API Configuration
    api_host: str = Field("localhost", alias="API_HOST")
    api_port: int = Field(8000, alias="API_PORT")

    # API rate limiting
    rate_limit_enabled: bool = Field(True)
    rate_limit_requests: int = Field(100)
    rate_limit_window: int = Field(60)

    # Cache Configuration
    cache_max_size: int = Field(1000, alias="CACHE_MAX_SIZE")

    # Feature flags
    feature_auto_tagging: bool = Field(True)
    feature_quality_scoring: bool = Field(True)
    feature_ai_generation: bool = Field(False)
    feature_batch_processing: bool = Field(True)

    @model_validator(mode="after")
    def _set_directories(self) -> "Settings":
        """Populate directory attributes if they were not provided."""

        package_root = Path(__file__).resolve().parent.parent

        if self.config_dir is None:
            self.config_dir = package_root / "resources"

        directory_map = {
            "templates_dir": self.base_dir / "templates",
            "cache_dir": self.base_dir / ".cache",
            "logs_dir": self.base_dir / "logs",
            "output_dir": self.base_dir / "output",
        }
        for attr, default_path in directory_map.items():
            if getattr(self, attr) is None:
                setattr(self, attr, default_path)
        return self

    @field_validator("hf_token", "huggingface_api_token")
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
        # Use either token field (prefer hf_token, fallback to huggingface_api_token)
        token = self.hf_token or self.huggingface_api_token
        if token:
            headers["Authorization"] = f"Bearer {token.get_secret_value()}"
        return headers

    def to_dict(self, *, exclude_secrets: bool = True) -> Dict[str, Any]:
        """Convert settings to dictionary."""

        data = self.model_dump()
        if exclude_secrets:
            data.pop("hf_token", None)
            data.pop("huggingface_api_token", None)
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
