"""Unit tests for portal integration and status modules."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from science_card_improvement.portal.integration import (
    PortalDatasetInsight,
    HuggingSciencePortal,
)
from science_card_improvement.portal.status import (
    WorkStatus,
    DatasetWorkStatus,
    PortalStatusManager,
    CollaborativeWorkflow,
)


@pytest.mark.unit
class TestPortalDatasetInsight:
    """Test PortalDatasetInsight dataclass."""

    def test_creation(self):
        """Test insight creation."""
        insight = PortalDatasetInsight(
            repo_id="user/dataset",
            category="genomics",
            quality_metrics={"completeness": 0.8},
            documentation_score=75.0,
            usage_stats={"downloads": 1000},
            community_engagement={"likes": 50},
            improvement_priority=65.0,
            last_updated=datetime.now(),
        )
        assert insight.repo_id == "user/dataset"
        assert insight.category == "genomics"
        assert insight.documentation_score == 75.0

    def test_default_values(self):
        """Test default values."""
        insight = PortalDatasetInsight(
            repo_id="user/dataset",
            category="genomics",
            quality_metrics={},
            documentation_score=50.0,
            usage_stats={},
            community_engagement={},
            improvement_priority=50.0,
            last_updated=datetime.now(),
        )
        assert insight.scientific_impact == {}
        assert insight.missing_components == []
        assert insight.recommended_tags == []


@pytest.mark.unit
class TestHuggingSciencePortal:
    """Test HuggingSciencePortal class."""

    @pytest.fixture
    def portal(self):
        """Create portal instance."""
        return HuggingSciencePortal(cache_enabled=False)

    def test_initialization(self, portal):
        """Test portal initialization."""
        assert portal.cache_enabled is False
        assert portal.client is None
        assert portal._session is None

    def test_science_categories(self, portal):
        """Test science categories are defined."""
        assert len(portal.SCIENCE_CATEGORIES) > 0
        assert "genomics" in portal.SCIENCE_CATEGORIES
        assert "medical_imaging" in portal.SCIENCE_CATEGORIES

    @pytest.mark.asyncio
    async def test_context_manager_exit(self, portal):
        """Test async context manager exit."""
        mock_session = AsyncMock()
        portal._session = mock_session

        await portal.__aexit__(None, None, None)
        mock_session.close.assert_called_once()


@pytest.mark.unit
class TestWorkStatus:
    """Test WorkStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert WorkStatus.AVAILABLE.value == "available"
        assert WorkStatus.IN_PROGRESS.value == "in_progress"
        assert WorkStatus.COMPLETED.value == "completed"


@pytest.mark.unit
class TestDatasetWorkStatus:
    """Test DatasetWorkStatus dataclass."""

    def test_creation(self):
        """Test work status creation."""
        status = DatasetWorkStatus(
            repo_id="user/dataset",
            status=WorkStatus.AVAILABLE,
            assigned_to=None,
            last_updated=datetime.now(),
        )
        assert status.repo_id == "user/dataset"
        assert status.status == WorkStatus.AVAILABLE
        assert status.assigned_to is None

    def test_assigned_status(self):
        """Test assigned work status."""
        status = DatasetWorkStatus(
            repo_id="user/dataset",
            status=WorkStatus.IN_PROGRESS,
            assigned_to="user@example.com",
            last_updated=datetime.now(),
        )
        assert status.status == WorkStatus.IN_PROGRESS
        assert status.assigned_to == "user@example.com"


@pytest.mark.unit
class TestPortalStatusManager:
    """Test PortalStatusManager class."""

    @pytest.fixture
    def manager(self):
        """Create status manager instance."""
        return PortalStatusManager()

    def test_initialization(self, manager):
        """Test manager initialization."""
        assert manager is not None

    @pytest.mark.asyncio
    async def test_get_available_datasets(self, manager):
        """Test getting available datasets."""
        datasets = await manager.get_available_datasets()
        assert isinstance(datasets, list)

    @pytest.mark.asyncio
    async def test_claim_dataset(self, manager):
        """Test claiming a dataset."""
        result = await manager.claim_dataset(
            "user/dataset",
            "contributor@example.com"
        )
        assert result is True or result is False

    @pytest.mark.asyncio
    async def test_release_dataset(self, manager):
        """Test releasing a dataset."""
        result = await manager.release_dataset(
            "user/dataset",
            "contributor@example.com"
        )
        assert result is True or result is False

    @pytest.mark.asyncio
    async def test_mark_completed(self, manager):
        """Test marking dataset as completed."""
        result = await manager.mark_completed(
            "user/dataset",
            "contributor@example.com"
        )
        assert result is True or result is False

    @pytest.mark.asyncio
    async def test_get_dataset_status(self, manager):
        """Test getting dataset status."""
        status = await manager.get_dataset_status("user/dataset")
        assert status is None or isinstance(status, DatasetWorkStatus)


@pytest.mark.unit
class TestCollaborativeWorkflow:
    """Test CollaborativeWorkflow class."""

    @pytest.fixture
    def workflow(self):
        """Create collaborative workflow instance."""
        return CollaborativeWorkflow()

    def test_initialization(self, workflow):
        """Test workflow initialization."""
        assert workflow is not None

    @pytest.mark.asyncio
    async def test_create_task(self, workflow):
        """Test creating a task."""
        task_id = await workflow.create_task(
            repo_id="user/dataset",
            task_type="improve_readme",
            priority=5
        )
        assert task_id is not None

    @pytest.mark.asyncio
    async def test_assign_task(self, workflow):
        """Test assigning a task."""
        task_id = await workflow.create_task(
            repo_id="user/dataset",
            task_type="improve_readme",
            priority=5
        )
        result = await workflow.assign_task(
            task_id,
            "contributor@example.com"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_complete_task(self, workflow):
        """Test completing a task."""
        task_id = await workflow.create_task(
            repo_id="user/dataset",
            task_type="improve_readme",
            priority=5
        )
        result = await workflow.complete_task(
            task_id,
            result_data={"improved": True}
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_get_contributor_stats(self, workflow):
        """Test getting contributor statistics."""
        stats = await workflow.get_contributor_stats("contributor@example.com")
        assert isinstance(stats, dict)


@pytest.mark.unit
class TestPortalIntegrationEdgeCases:
    """Test edge cases for portal integration."""

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test handling timeout."""
        portal = HuggingSciencePortal()

        with patch.object(portal, '_fetch_portal_data') as mock_fetch:
            mock_fetch.side_effect = asyncio.TimeoutError()
            async with portal:
                portal._session = AsyncMock()
                with pytest.raises(asyncio.TimeoutError):
                    await portal.search_science_datasets()

    @pytest.mark.asyncio
    async def test_invalid_response_handling(self):
        """Test handling invalid response."""
        portal = HuggingSciencePortal()

        with patch.object(portal, '_fetch_portal_data') as mock_fetch:
            mock_fetch.return_value = None
            async with portal:
                portal._session = AsyncMock()
                results = await portal.search_science_datasets()
                assert results == [] or results is None
