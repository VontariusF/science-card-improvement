"""Unit tests for repository discovery functionality."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from science_card_improvement.discovery.repository import RepositoryDiscovery, RepositoryMetadata
from science_card_improvement.exceptions.custom_exceptions import NetworkError, RateLimitError


@pytest.mark.unit
class TestRepositoryMetadata:
    """Test RepositoryMetadata class."""

    def test_metadata_creation(self, sample_repository_metadata):
        """Test metadata object creation."""
        assert sample_repository_metadata.repo_id == "test-org/test-dataset"
        assert sample_repository_metadata.repo_type == "dataset"
        assert sample_repository_metadata.priority_score == 65.0

    def test_metadata_to_dict(self, sample_repository_metadata):
        """Test metadata serialization."""
        data = sample_repository_metadata.to_dict()
        assert isinstance(data, dict)
        assert data["repo_id"] == "test-org/test-dataset"
        assert "created_at" in data
        assert "metrics" in data

    def test_metadata_from_dict(self):
        """Test metadata deserialization."""
        data = {
            "repo_id": "test/repo",
            "repo_type": "model",
            "title": "Test",
            "description": "Test description",
            "downloads": 100,
            "likes": 10,
            "priority_score": 50.0,
        }
        metadata = RepositoryMetadata.from_dict(data)
        assert metadata.repo_id == "test/repo"
        assert metadata.downloads == 100

    def test_calculate_priority_score(self):
        """Test priority score calculation."""
        metadata = RepositoryMetadata(
            repo_id="test/repo",
            repo_type="dataset",
            title="Test",
            description="Test",
            downloads=5000,
            likes=100,
            has_readme=False,
        )
        score = metadata.calculate_priority_score()
        assert score > 40  # High priority for missing README
        assert metadata.priority_score == score

    def test_priority_score_with_short_readme(self):
        """Test priority score with short README."""
        metadata = RepositoryMetadata(
            repo_id="test/repo",
            repo_type="dataset",
            title="Test",
            description="Test",
            downloads=1000,
            likes=50,
            has_readme=True,
            readme_length=200,
        )
        score = metadata.calculate_priority_score()
        assert 30 <= score <= 60  # Medium-high priority


@pytest.mark.unit
@pytest.mark.asyncio
class TestRepositoryDiscovery:
    """Test RepositoryDiscovery class."""

    async def test_discovery_initialization(self, test_settings):
        """Test discovery client initialization."""
        discovery = RepositoryDiscovery(token="test_token")
        assert discovery.api is not None
        assert discovery.parallel_workers > 0
        assert len(discovery.science_keywords) > 0

    async def test_discover_repositories_datasets(self, discovery_client, mock_hf_api):
        """Test discovering datasets."""
        repos = await discovery_client.discover_repositories(
            repo_type="dataset",
            limit=10,
        )
        assert isinstance(repos, list)
        assert all(isinstance(r, RepositoryMetadata) for r in repos)
        assert all(r.repo_type == "dataset" for r in repos)

    async def test_discover_repositories_models(self, discovery_client, mock_hf_api):
        """Test discovering models."""
        repos = await discovery_client.discover_repositories(
            repo_type="model",
            limit=10,
        )
        assert isinstance(repos, list)
        assert all(r.repo_type == "model" for r in repos)

    async def test_discover_repositories_both(self, discovery_client, mock_hf_api):
        """Test discovering both datasets and models."""
        repos = await discovery_client.discover_repositories(
            repo_type="both",
            limit=10,
        )
        assert isinstance(repos, list)
        # Should have both types
        repo_types = {r.repo_type for r in repos}
        assert "dataset" in repo_types or "model" in repo_types

    async def test_discover_with_keywords(self, discovery_client, mock_hf_api):
        """Test discovery with custom keywords."""
        repos = await discovery_client.discover_repositories(
            repo_type="dataset",
            limit=5,
            keywords=["biology", "genomics"],
        )
        assert isinstance(repos, list)
        assert len(repos) <= 5

    async def test_discover_with_filters(self, discovery_client, mock_hf_api):
        """Test discovery with filters."""
        # Create mock repos with different download counts
        mock_repos = [
            RepositoryMetadata(
                repo_id=f"test/repo{i}",
                repo_type="dataset",
                title=f"Test {i}",
                description="Test",
                downloads=i * 100,
            )
            for i in range(10)
        ]

        with patch.object(
            discovery_client,
            "_discover_datasets",
            return_value=asyncio.coroutine(lambda *args: mock_repos)(),
        ):
            repos = await discovery_client.discover_repositories(
                repo_type="dataset",
                limit=10,
                filters={"min_downloads": 500},
            )

            # Should only return repos with downloads >= 500
            assert all(r.downloads >= 500 for r in repos)

    async def test_discover_with_sorting(self, discovery_client):
        """Test discovery with different sorting options."""
        mock_repos = [
            RepositoryMetadata(
                repo_id=f"test/repo{i}",
                repo_type="dataset",
                title=f"Test {i}",
                description="Test",
                downloads=i * 100,
                likes=i * 10,
                priority_score=float(i * 5),
            )
            for i in range(5)
        ]

        with patch.object(
            discovery_client,
            "_discover_datasets",
            return_value=asyncio.coroutine(lambda *args: mock_repos)(),
        ):
            # Sort by downloads
            repos = await discovery_client.discover_repositories(
                repo_type="dataset",
                limit=10,
                sort_by="downloads",
            )
            assert repos[0].downloads >= repos[-1].downloads

            # Sort by priority
            repos = await discovery_client.discover_repositories(
                repo_type="dataset",
                limit=10,
                sort_by="priority",
            )
            assert repos[0].priority_score >= repos[-1].priority_score

    async def test_network_error_retry(self, discovery_client):
        """Test retry on network errors."""
        with patch.object(
            discovery_client,
            "_search_datasets_sync",
            side_effect=[NetworkError("Network error"), []],
        ):
            # Should retry and eventually succeed
            repos = await discovery_client.discover_repositories(
                repo_type="dataset",
                limit=5,
            )
            assert isinstance(repos, list)

    async def test_rate_limit_error_retry(self, discovery_client):
        """Test retry on rate limit errors."""
        with patch.object(
            discovery_client,
            "_search_datasets_sync",
            side_effect=[RateLimitError("Rate limited", retry_after=1), []],
        ):
            repos = await discovery_client.discover_repositories(
                repo_type="dataset",
                limit=5,
            )
            assert isinstance(repos, list)

    async def test_enrichment_with_readme(self, discovery_client, tmp_path):
        """Test metadata enrichment with README."""
        # Create mock README file
        readme_path = tmp_path / "README.md"
        readme_content = "# Test Dataset\n\nThis is a test dataset with comprehensive documentation."
        readme_path.write_text(readme_content)

        with patch.object(
            discovery_client.api,
            "hf_hub_download",
            return_value=str(readme_path),
        ):
            repo = RepositoryMetadata(
                repo_id="test/repo",
                repo_type="dataset",
                title="Test",
                description="Test",
            )

            enriched = discovery_client._enrich_single_repository(repo)
            assert enriched.has_readme is True
            assert enriched.readme_length == len(readme_content)
            assert enriched.readme_quality_score > 0

    async def test_enrichment_without_readme(self, discovery_client):
        """Test metadata enrichment without README."""
        with patch.object(
            discovery_client.api,
            "hf_hub_download",
            side_effect=Exception("File not found"),
        ):
            repo = RepositoryMetadata(
                repo_id="test/repo",
                repo_type="dataset",
                title="Test",
                description="Test",
            )

            enriched = discovery_client._enrich_single_repository(repo)
            assert enriched.has_readme is False
            assert "Missing README.md file" in enriched.issues

    def test_readme_quality_assessment(self, discovery_client, sample_readme):
        """Test README quality assessment."""
        score = discovery_client._assess_readme_quality(sample_readme)
        assert 0 <= score <= 1
        assert score > 0.5  # Should be good quality

    def test_readme_issue_identification(self, discovery_client):
        """Test identifying README issues."""
        # Short README
        short_readme = "# Test\n\nShort description."
        issues = discovery_client._identify_readme_issues(short_readme)
        assert any("too short" in issue for issue in issues)

        # Missing sections
        incomplete_readme = "# Test Dataset\n\nThis is a test dataset."
        issues = discovery_client._identify_readme_issues(incomplete_readme)
        assert any("license" in issue.lower() for issue in issues)
        assert any("citation" in issue.lower() for issue in issues)

    def test_suggestion_generation(self, discovery_client):
        """Test generating improvement suggestions."""
        repo = RepositoryMetadata(
            repo_id="test/repo",
            repo_type="dataset",
            title="Test",
            description="Test dataset",
            has_readme=False,
        )

        suggestions = discovery_client._generate_suggestions(repo)
        assert len(suggestions) > 0
        assert any("README" in s for s in suggestions)

    async def test_export_results_json(self, discovery_client, tmp_path):
        """Test exporting results to JSON."""
        repos = [
            RepositoryMetadata(
                repo_id=f"test/repo{i}",
                repo_type="dataset",
                title=f"Test {i}",
                description="Test",
            )
            for i in range(3)
        ]

        output_file = tmp_path / "results.json"
        await discovery_client.export_results(repos, output_file, format="json")

        assert output_file.exists()
        import json
        with open(output_file) as f:
            data = json.load(f)
        assert len(data) == 3
        assert data[0]["repo_id"] == "test/repo0"

    async def test_export_results_csv(self, discovery_client, tmp_path):
        """Test exporting results to CSV."""
        repos = [
            RepositoryMetadata(
                repo_id=f"test/repo{i}",
                repo_type="dataset",
                title=f"Test {i}",
                description="Test",
            )
            for i in range(3)
        ]

        output_file = tmp_path / "results.csv"
        await discovery_client.export_results(repos, output_file, format="csv")

        assert output_file.exists()
        import pandas as pd
        df = pd.read_csv(output_file)
        assert len(df) == 3
        assert "repo_id" in df.columns

    def test_statistics_tracking(self, discovery_client):
        """Test statistics tracking."""
        initial_stats = discovery_client.get_statistics()
        assert "total_discovered" in initial_stats
        assert "api_calls" in initial_stats
        assert "errors" in initial_stats

        # Simulate API call
        discovery_client._search_datasets_sync("test", 10)
        updated_stats = discovery_client.get_statistics()
        assert updated_stats["api_calls"] > initial_stats["api_calls"]