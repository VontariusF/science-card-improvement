"""Pytest configuration and shared fixtures."""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch

import pytest
from faker import Faker
from huggingface_hub import DatasetInfo, ModelInfo

from science_card_improvement.config.settings import Settings, reset_settings
from science_card_improvement.discovery.repository import RepositoryDiscovery, RepositoryMetadata
from science_card_improvement.utils.cache import CacheManager
from science_card_improvement.utils.logger import setup_logging


# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def faker() -> Faker:
    """Provide Faker instance for generating test data."""
    return Faker()


@pytest.fixture
def test_settings() -> Settings:
    """Provide test settings."""
    reset_settings()
    settings = Settings(
        debug=True,
        environment="test",
        hf_token="test_token_12345",
        cache_dir=Path("/tmp/test_cache"),
        logs_dir=Path("/tmp/test_logs"),
        output_dir=Path("/tmp/test_output"),
        monitoring_enabled=False,
        log_file_enabled=False,
    )
    settings.create_directories()
    return settings


@pytest.fixture
def mock_hf_api():
    """Mock Hugging Face API."""
    with patch("science_card_improvement.discovery.repository.HfApi") as mock_api:
        # Mock list_datasets
        mock_api.return_value.list_datasets.return_value = [
            create_mock_dataset_info("user/dataset1"),
            create_mock_dataset_info("user/dataset2"),
        ]

        # Mock list_models
        mock_api.return_value.list_models.return_value = [
            create_mock_model_info("user/model1"),
            create_mock_model_info("user/model2"),
        ]

        # Mock hf_hub_download
        mock_api.return_value.hf_hub_download.return_value = "/tmp/README.md"

        # Mock list_repo_files
        mock_api.return_value.list_repo_files.return_value = [
            "README.md",
            "data/train.csv",
            "data/test.csv",
        ]

        yield mock_api


@pytest.fixture
def sample_repository_metadata() -> RepositoryMetadata:
    """Create sample repository metadata."""
    return RepositoryMetadata(
        repo_id="test-org/test-dataset",
        repo_type="dataset",
        title="Test Dataset",
        description="A test dataset for unit testing",
        tags=["test", "science", "biology"],
        author="test-org",
        downloads=1000,
        likes=50,
        has_readme=True,
        readme_length=1500,
        readme_quality_score=0.75,
        license="MIT",
        issues=["Missing citation"],
        suggestions=["Add usage examples"],
        priority_score=65.0,
    )


@pytest.fixture
def discovery_client(test_settings, mock_hf_api) -> RepositoryDiscovery:
    """Create discovery client for testing."""
    return RepositoryDiscovery(token="test_token", cache_enabled=False)


@pytest.fixture
def cache_manager(tmp_path) -> CacheManager:
    """Create cache manager for testing."""
    return CacheManager(cache_dir=tmp_path / "cache", default_ttl=60)


@pytest.fixture
def sample_readme() -> str:
    """Sample README content for testing."""
    return """
# Test Dataset

## Description
This is a comprehensive test dataset for scientific research.

## Dataset Structure
The dataset contains the following files:
- train.csv: Training data (10,000 samples)
- test.csv: Test data (2,000 samples)
- validation.csv: Validation data (1,000 samples)

## Installation
```python
from datasets import load_dataset
dataset = load_dataset("test-org/test-dataset")
```

## Usage
```python
# Load the dataset
dataset = load_dataset("test-org/test-dataset")

# Access training data
train_data = dataset['train']

# Iterate through samples
for sample in train_data:
    print(sample)
```

## License
This dataset is released under the MIT License.

## Citation
```bibtex
@dataset{test_dataset_2024,
  title={Test Dataset},
  author={Test Author},
  year={2024},
  publisher={Hugging Face}
}
```

## Acknowledgments
We thank all contributors to this dataset.
"""


@pytest.fixture
def sample_config_files(tmp_path) -> Path:
    """Create sample configuration files."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)

    # Science keywords
    keywords = {
        "keywords": [
            "biology",
            "chemistry",
            "physics",
            "genomics",
            "proteomics",
        ]
    }
    with open(config_dir / "science_keywords.json", "w") as f:
        json.dump(keywords, f)

    # Domain tags
    domain_tags = {
        "biology": ["biology", "genomics", "proteomics"],
        "chemistry": ["chemistry", "molecular"],
        "physics": ["physics", "quantum"],
    }
    with open(config_dir / "domain_tags.json", "w") as f:
        json.dump(domain_tags, f)

    return config_dir


@pytest.fixture
def mock_api_responses():
    """Mock API responses for testing."""
    return {
        "dataset_info": {
            "id": "test-org/test-dataset",
            "author": "test-org",
            "sha": "abc123",
            "lastModified": "2024-01-01T00:00:00Z",
            "private": False,
            "downloads": 1000,
            "likes": 50,
            "tags": ["science", "biology"],
            "cardData": {
                "license": "mit",
                "language": ["en"],
                "pretty_name": "Test Dataset",
            },
        },
        "model_info": {
            "id": "test-org/test-model",
            "author": "test-org",
            "sha": "def456",
            "lastModified": "2024-01-01T00:00:00Z",
            "private": False,
            "downloads": 500,
            "likes": 25,
            "tags": ["transformers", "nlp"],
            "pipeline_tag": "text-classification",
            "cardData": {
                "license": "apache-2.0",
                "language": ["en"],
                "model_name": "Test Model",
            },
        },
    }


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment between tests."""
    # Reset settings singleton
    reset_settings()

    # Clear environment variables
    test_env_vars = [
        "HF_TOKEN",
        "DEBUG",
        "ENVIRONMENT",
        "LOG_LEVEL",
    ]
    for var in test_env_vars:
        os.environ.pop(var, None)

    yield

    # Cleanup after test
    reset_settings()


@pytest.fixture
def async_mock():
    """Create async mock helper."""
    def _async_mock(return_value=None):
        future = asyncio.Future()
        future.set_result(return_value)
        return future
    return _async_mock


# Helper functions

def create_mock_dataset_info(repo_id: str) -> DatasetInfo:
    """Create mock DatasetInfo object."""
    mock_info = MagicMock(spec=DatasetInfo)
    mock_info.id = repo_id
    mock_info.author = repo_id.split("/")[0] if "/" in repo_id else "unknown"
    mock_info.downloads = 1000
    mock_info.likes = 50
    mock_info.tags = ["science", "test"]
    mock_info.cardData = {
        "license": "mit",
        "pretty_name": repo_id.split("/")[-1].replace("-", " ").title(),
    }
    return mock_info


def create_mock_model_info(repo_id: str) -> ModelInfo:
    """Create mock ModelInfo object."""
    mock_info = MagicMock(spec=ModelInfo)
    mock_info.id = repo_id
    mock_info.author = repo_id.split("/")[0] if "/" in repo_id else "unknown"
    mock_info.downloads = 500
    mock_info.likes = 25
    mock_info.tags = ["transformers", "test"]
    mock_info.pipeline_tag = "text-classification"
    mock_info.cardData = {
        "license": "apache-2.0",
        "model_name": repo_id.split("/")[-1].replace("-", " ").title(),
    }
    return mock_info


def create_test_file(path: Path, content: str = "") -> Path:
    """Create a test file with content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content or "Test content")
    return path


# Markers for test categorization

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Tests that take > 1s")
    config.addinivalue_line("markers", "requires_hf_token: Tests requiring HF token")
    config.addinivalue_line("markers", "asyncio: Async tests")