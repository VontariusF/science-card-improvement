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
        assert WorkStatus.NOT_STARTED.value == "not_started"
        assert WorkStatus.IN_PROGRESS.value == "in_progress"
        assert WorkStatus.REVIEWING.value == "reviewing"
        assert WorkStatus.COMPLETED.value == "completed"
        assert WorkStatus.NEEDS_HELP.value == "needs_help"
        assert WorkStatus.BLOCKED.value == "blocked"

    def test_all_statuses(self):
        """Test all status options exist."""
        statuses = list(WorkStatus)
        assert len(statuses) == 6


@pytest.mark.unit
class TestDatasetWorkStatus:
    """Test DatasetWorkStatus dataclass."""

    def test_creation(self):
        """Test work status creation."""
        status = DatasetWorkStatus(
            dataset_id="user/dataset",
            user_id="contributor",
            status=WorkStatus.NOT_STARTED,
        )
        assert status.dataset_id == "user/dataset"
        assert status.user_id == "contributor"
        assert status.status == WorkStatus.NOT_STARTED

    def test_in_progress_status(self):
        """Test in progress work status."""
        status = DatasetWorkStatus(
            dataset_id="user/dataset",
            user_id="user@example.com",
            status=WorkStatus.IN_PROGRESS,
            started_at=datetime.now(),
            notes="Working on improvements",
        )
        assert status.status == WorkStatus.IN_PROGRESS
        assert status.notes == "Working on improvements"

    def test_completed_status(self):
        """Test completed work status."""
        status = DatasetWorkStatus(
            dataset_id="user/dataset",
            user_id="user@example.com",
            status=WorkStatus.COMPLETED,
            pr_url="https://github.com/user/dataset/pull/1",
            improvement_score=0.85,
        )
        assert status.status == WorkStatus.COMPLETED
        assert status.pr_url is not None
        assert status.improvement_score == 0.85


@pytest.mark.unit
class TestPortalStatusManager:
    """Test PortalStatusManager class."""

    @pytest.fixture
    def manager(self):
        """Create status manager instance."""
        with patch('science_card_improvement.portal.status.get_settings') as mock_settings:
            mock_settings.return_value.hf_username = "test_user"
            return PortalStatusManager(user_id="test_user")

    def test_initialization(self, manager):
        """Test manager initialization."""
        assert manager is not None
        assert manager.user_id == "test_user"

    def test_portal_url(self, manager):
        """Test portal URL is defined."""
        assert manager.PORTAL_URL is not None
        assert "huggingface.co" in manager.PORTAL_URL

    def test_api_endpoint(self, manager):
        """Test API endpoint is defined."""
        assert manager.API_ENDPOINT is not None


@pytest.mark.unit
class TestCollaborativeWorkflow:
    """Test CollaborativeWorkflow class."""

    @pytest.fixture
    def workflow(self):
        """Create collaborative workflow instance."""
        with patch('science_card_improvement.portal.status.get_settings'):
            return CollaborativeWorkflow(user_id="test_user")

    def test_initialization(self, workflow):
        """Test workflow initialization."""
        assert workflow is not None


@pytest.mark.unit
class TestPortalIntegrationEdgeCases:
    """Test edge cases for portal integration."""

    def test_insight_with_missing_components(self):
        """Test insight with missing components."""
        insight = PortalDatasetInsight(
            repo_id="user/dataset",
            category="biology",
            quality_metrics={"completeness": 0.3},
            documentation_score=30.0,
            usage_stats={"downloads": 100},
            community_engagement={},
            improvement_priority=80.0,
            last_updated=datetime.now(),
            missing_components=["citation", "license", "examples"],
        )
        assert len(insight.missing_components) == 3
        assert insight.improvement_priority > 50

    def test_insight_with_recommended_tags(self):
        """Test insight with recommended tags."""
        insight = PortalDatasetInsight(
            repo_id="user/dataset",
            category="genomics",
            quality_metrics={},
            documentation_score=50.0,
            usage_stats={},
            community_engagement={},
            improvement_priority=50.0,
            last_updated=datetime.now(),
            recommended_tags=["single-cell", "rna-seq", "transcriptomics"],
        )
        assert len(insight.recommended_tags) == 3

    def test_work_status_transitions(self):
        """Test work status can transition."""
        status = DatasetWorkStatus(
            dataset_id="user/dataset",
            user_id="user",
            status=WorkStatus.NOT_STARTED,
        )
        # Simulate status transition
        status.status = WorkStatus.IN_PROGRESS
        assert status.status == WorkStatus.IN_PROGRESS

        status.status = WorkStatus.REVIEWING
        assert status.status == WorkStatus.REVIEWING

        status.status = WorkStatus.COMPLETED
        assert status.status == WorkStatus.COMPLETED
