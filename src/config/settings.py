"""Application configuration and settings management."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseSettings, Field, validator
from pydantic.types import SecretStr


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    app_name: str = "Science Card Improvement"
    app_version: str = "1.0.0"
    debug: bool = Field(False, env="DEBUG")
    environment: str = Field("production", env="ENVIRONMENT")

    # Hugging Face
    hf_token: Optional[SecretStr] = Field(None, env="HF_TOKEN")
    hf_endpoint: str = Field("https://huggingface.co", env="HF_ENDPOINT")
    hf_api_timeout: int = Field(30, env="HF_API_TIMEOUT")
    hf_max_retries: int = Field(3, env="HF_MAX_RETRIES")

    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    config_dir: Path = Field(None)
    templates_dir: Path = Field(None)
    cache_dir: Path = Field(None)
    logs_dir: Path = Field(None)
    output_dir: Path = Field(None)

    # Discovery settings
    discovery_batch_size: int = Field(100, env="DISCOVERY_BATCH_SIZE")
    discovery_max_workers: int = Field(10, env="DISCOVERY_MAX_WORKERS")
    discovery_cache_ttl: int = Field(3600, env="DISCOVERY_CACHE_TTL")

    # Assessment settings
    assessment_min_readme_length: int = Field(300, env="ASSESSMENT_MIN_README_LENGTH")
    assessment_required_sections: List[str] = Field(
        default_factory=lambda: [
            "description",
            "dataset_structure",
            "license",
            "citation",
        ]
    )

    # Generation settings
    generation_model: str = Field("gpt-4", env="GENERATION_MODEL")
    generation_temperature: float = Field(0.7, env="GENERATION_TEMPERATURE")
    generation_max_tokens: int = Field(4000, env="GENERATION_MAX_TOKENS")

    # Submission settings
    submission_branch_prefix: str = Field("improve-card", env="SUBMISSION_BRANCH_PREFIX")
    submission_pr_template: str = Field("pr_template.md", env="SUBMISSION_PR_TEMPLATE")
    submission_dry_run: bool = Field(False, env="SUBMISSION_DRY_RUN")

    # Monitoring
    monitoring_enabled: bool = Field(True, env="MONITORING_ENABLED")
    monitoring_port: int = Field(8080, env="MONITORING_PORT")
    monitoring_metrics_path: str = Field("/metrics", env="MONITORING_METRICS_PATH")

    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    log_file_enabled: bool = Field(True, env="LOG_FILE_ENABLED")
    log_file_rotation: str = Field("1 day", env="LOG_FILE_ROTATION")
    log_file_retention: str = Field("30 days", env="LOG_FILE_RETENTION")

    # Database (for future scalability)
    database_url: Optional[str] = Field(None, env="DATABASE_URL")
    database_pool_size: int = Field(10, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(20, env="DATABASE_MAX_OVERFLOW")

    # Redis cache (for future scalability)
    redis_url: Optional[str] = Field(None, env="REDIS_URL")
    redis_ttl: int = Field(3600, env="REDIS_TTL")

    # API rate limiting
    rate_limit_enabled: bool = Field(True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(60, env="RATE_LIMIT_WINDOW")

    # Feature flags
    feature_auto_tagging: bool = Field(True, env="FEATURE_AUTO_TAGGING")
    feature_quality_scoring: bool = Field(True, env="FEATURE_QUALITY_SCORING")
    feature_ai_generation: bool = Field(False, env="FEATURE_AI_GENERATION")
    feature_batch_processing: bool = Field(True, env="FEATURE_BATCH_PROCESSING")

    @validator("config_dir", "templates_dir", "cache_dir", "logs_dir", "output_dir", pre=True, always=True)
    def set_directories(cls, v, values, field):
        """Set default directories based on base_dir."""
        if v is None:
            base_dir = values.get("base_dir", Path.cwd())
            directory_map = {
                "config_dir": base_dir / "config",
                "templates_dir": base_dir / "templates",
                "cache_dir": base_dir / ".cache",
                "logs_dir": base_dir / "logs",
                "output_dir": base_dir / "output",
            }
            return directory_map.get(field.name)
        return v

    @validator("hf_token")
    def validate_hf_token(cls, v):
        """Validate Hugging Face token if provided."""
        if v and len(v.get_secret_value()) < 10:
            raise ValueError("Invalid Hugging Face token format")
        return v

    def create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for dir_path in [self.cache_dir, self.logs_dir, self.output_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def get_hf_headers(self) -> Dict[str, str]:
        """Get headers for Hugging Face API requests."""
        headers = {"User-Agent": f"{self.app_name}/{self.app_version}"}
        if self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token.get_secret_value()}"
        return headers

    def to_dict(self, exclude_secrets: bool = True) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        data = self.dict()
        if exclude_secrets:
            data.pop("hf_token", None)
            data.pop("database_url", None)
            data.pop("redis_url", None)
        return data

    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


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