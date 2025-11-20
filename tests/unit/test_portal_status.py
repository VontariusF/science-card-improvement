"""Comprehensive unit tests for portal status module."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from science_card_improvement.portal.status import (
    WorkStatus,
    DatasetWorkStatus,
    PortalStatusManager,
    CollaborativeWorkflow,
)


@pytest.mark.unit
class TestWorkStatusEnum:
    """Test WorkStatus enum."""

    def test_all_status_values(self):
        """Test all status values exist."""
        assert WorkStatus.NOT_STARTED.value == "not_started"
        assert WorkStatus.IN_PROGRESS.value == "in_progress"
        assert WorkStatus.REVIEWING.value == "reviewing"
        assert WorkStatus.COMPLETED.value == "completed"
        assert WorkStatus.NEEDS_HELP.value == "needs_help"
        assert WorkStatus.BLOCKED.value == "blocked"

    def test_status_count(self):
        """Test we have expected number of statuses."""
        assert len(WorkStatus) == 6


@pytest.mark.unit
class TestDatasetWorkStatusDataclass:
    """Test DatasetWorkStatus dataclass."""

    def test_creation_minimal(self):
        """Test creating with minimal fields."""
        status = DatasetWorkStatus(
            dataset_id="user/dataset",
            user_id="contributor",
            status=WorkStatus.NOT_STARTED,
        )
        assert status.dataset_id == "user/dataset"
        assert status.user_id == "contributor"
        assert status.status == WorkStatus.NOT_STARTED

    def test_creation_full(self):
        """Test creating with all fields."""
        now = datetime.now()
        status = DatasetWorkStatus(
            dataset_id="user/dataset",
            user_id="contributor",
            status=WorkStatus.IN_PROGRESS,
            started_at=now,
            last_updated=now,
            notes="Working on it",
            estimated_completion=now,
            pr_url="https://github.com/pull/1",
            improvement_score=25.0,
        )
        assert status.started_at == now
        assert status.notes == "Working on it"
        assert status.pr_url == "https://github.com/pull/1"
        assert status.improvement_score == 25.0


@pytest.mark.unit
class TestPortalStatusManager:
    """Test PortalStatusManager class."""

    def test_initialization_with_user_id(self):
        """Test initialization with explicit user ID."""
        with patch('science_card_improvement.portal.status.get_settings') as mock_settings:
            mock_settings.return_value.hf_username = "default_user"
            manager = PortalStatusManager(user_id="test_user")
            assert manager.user_id == "test_user"

    def test_initialization_without_user_id(self):
        """Test initialization uses settings username."""
        with patch('science_card_improvement.portal.status.get_settings') as mock_settings:
            mock_settings.return_value.hf_username = "settings_user"
            manager = PortalStatusManager()
            assert manager.user_id == "settings_user"

    def test_portal_urls(self):
        """Test portal URLs are defined."""
        assert PortalStatusManager.PORTAL_URL.startswith("https://")
        assert PortalStatusManager.API_ENDPOINT.startswith("https://")

    @pytest.mark.asyncio
    async def test_context_manager_entry(self):
        """Test async context manager entry."""
        with patch('science_card_improvement.portal.status.get_settings'):
            with patch('science_card_improvement.portal.status.aiohttp.ClientSession'):
                with patch('science_card_improvement.portal.status.Client') as mock_client:
                    mock_client.side_effect = Exception("Connection failed")

                    manager = PortalStatusManager(user_id="test")
                    result = await manager.__aenter__()

                    assert result is manager

    @pytest.mark.asyncio
    async def test_context_manager_exit(self):
        """Test async context manager exit closes session."""
        with patch('science_card_improvement.portal.status.get_settings'):
            manager = PortalStatusManager(user_id="test")
            mock_session = AsyncMock()
            manager._session = mock_session

            await manager.__aexit__(None, None, None)

            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_claim_dataset_success(self):
        """Test claiming a dataset successfully."""
        with patch('science_card_improvement.portal.status.get_settings'):
            manager = PortalStatusManager(user_id="test_user")
            manager.client = MagicMock()
            manager.client.predict.return_value = {"success": True}

            success = await manager.claim_dataset(
                dataset_id="test/dataset",
                notes="Working on improvements",
                estimated_days=5
            )

            assert success is True
            manager.client.predict.assert_called_once()

    @pytest.mark.asyncio
    async def test_claim_dataset_failure(self):
        """Test claiming a dataset that's already taken."""
        with patch('science_card_improvement.portal.status.get_settings'):
            manager = PortalStatusManager(user_id="test_user")
            manager.client = MagicMock()
            manager.client.predict.return_value = {"success": False}

            success = await manager.claim_dataset("test/dataset")

            assert success is False

    @pytest.mark.asyncio
    async def test_claim_dataset_error(self):
        """Test claim dataset error handling."""
        with patch('science_card_improvement.portal.status.get_settings'):
            manager = PortalStatusManager(user_id="test_user")
            manager.client = MagicMock()
            manager.client.predict.side_effect = Exception("Error")

            success = await manager.claim_dataset("test/dataset")

            assert success is False

    @pytest.mark.asyncio
    async def test_update_status_success(self):
        """Test updating status successfully."""
        with patch('science_card_improvement.portal.status.get_settings'):
            manager = PortalStatusManager(user_id="test_user")
            manager.client = MagicMock()
            manager.client.predict.return_value = {"success": True}

            success = await manager.update_status(
                dataset_id="test/dataset",
                status=WorkStatus.REVIEWING,
                notes="Ready for review",
                pr_url="https://github.com/pull/1"
            )

            assert success is True

    @pytest.mark.asyncio
    async def test_check_availability_available(self):
        """Test checking availability when available."""
        with patch('science_card_improvement.portal.status.get_settings'):
            manager = PortalStatusManager(user_id="test_user")
            manager.client = MagicMock()
            manager.client.predict.return_value = {
                "available": True,
                "current_worker": None,
                "status": "not_started"
            }

            result = await manager.check_availability("test/dataset")

            assert result["available"] is True

    @pytest.mark.asyncio
    async def test_check_availability_error_returns_available(self):
        """Test error in check returns available as default."""
        with patch('science_card_improvement.portal.status.get_settings'):
            manager = PortalStatusManager(user_id="test_user")
            manager.client = MagicMock()
            manager.client.predict.side_effect = Exception("Error")

            result = await manager.check_availability("test/dataset")

            assert result["available"] is True

    @pytest.mark.asyncio
    async def test_get_my_datasets(self):
        """Test getting user's datasets."""
        with patch('science_card_improvement.portal.status.get_settings'):
            manager = PortalStatusManager(user_id="test_user")
            manager.client = MagicMock()
            manager.client.predict.return_value = [
                {"id": "dataset1", "status": "in_progress"},
                {"id": "dataset2", "status": "completed"}
            ]

            datasets = await manager.get_my_datasets()

            assert len(datasets) == 2

    @pytest.mark.asyncio
    async def test_search_minimal_datasets(self):
        """Test searching for minimal datasets."""
        with patch('science_card_improvement.portal.status.get_settings'):
            manager = PortalStatusManager(user_id="test_user")
            manager.client = MagicMock()
            manager.client.predict.return_value = [{"id": "minimal/dataset"}]

            datasets = await manager.search_minimal_datasets(limit=50)

            assert len(datasets) == 1

    @pytest.mark.asyncio
    async def test_get_dataset_metadata(self):
        """Test getting dataset metadata."""
        with patch('science_card_improvement.portal.status.get_settings'):
            manager = PortalStatusManager(user_id="test_user")
            manager.client = MagicMock()
            manager.client.predict.return_value = {
                "downloads": 1000,
                "size": "10GB",
                "doc_score": 60
            }

            metadata = await manager.get_dataset_metadata("test/dataset")

            assert metadata["downloads"] == 1000

    @pytest.mark.asyncio
    async def test_complete_work_success(self):
        """Test completing work successfully."""
        with patch('science_card_improvement.portal.status.get_settings'):
            manager = PortalStatusManager(user_id="test_user")
            manager.client = MagicMock()
            manager.client.predict.return_value = {"success": True}

            success = await manager.complete_work(
                dataset_id="test/dataset",
                pr_url="https://github.com/pull/1",
                before_score=40.0,
                after_score=80.0,
                improvements=["Added description", "Added citation"]
            )

            assert success is True


@pytest.mark.unit
class TestPortalStatusManagerHTTPFallbacks:
    """Test HTTP fallback methods."""

    @pytest.mark.asyncio
    async def test_http_update_status_success(self):
        """Test HTTP update status."""
        with patch('science_card_improvement.portal.status.get_settings'):
            manager = PortalStatusManager(user_id="test")

            mock_response = MagicMock()
            mock_response.status = 200

            mock_cm = MagicMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_cm.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.post.return_value = mock_cm
            manager._session = mock_session

            result = await manager._http_update_status({"dataset_id": "test"})

            assert result is True

    @pytest.mark.asyncio
    async def test_http_update_status_no_session(self):
        """Test HTTP update without session."""
        with patch('science_card_improvement.portal.status.get_settings'):
            manager = PortalStatusManager(user_id="test")
            manager._session = None

            result = await manager._http_update_status({})

            assert result is False

    @pytest.mark.asyncio
    async def test_http_check_status(self):
        """Test HTTP check status."""
        with patch('science_card_improvement.portal.status.get_settings'):
            manager = PortalStatusManager(user_id="test")

            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"available": False})

            mock_cm = MagicMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_cm.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get.return_value = mock_cm
            manager._session = mock_session

            result = await manager._http_check_status("test/dataset")

            assert result["available"] is False

    @pytest.mark.asyncio
    async def test_http_get_user_datasets(self):
        """Test HTTP get user datasets."""
        with patch('science_card_improvement.portal.status.get_settings'):
            manager = PortalStatusManager(user_id="test")

            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=[{"id": "dataset1"}])

            mock_cm = MagicMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
            mock_cm.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.get.return_value = mock_cm
            manager._session = mock_session

            result = await manager._http_get_user_datasets("test")

            assert len(result) == 1


@pytest.mark.unit
class TestCollaborativeWorkflow:
    """Test CollaborativeWorkflow class."""

    def test_initialization(self):
        """Test workflow initialization."""
        with patch('science_card_improvement.portal.status.get_settings'):
            workflow = CollaborativeWorkflow(user_id="test_user")
            assert workflow.user_id == "test_user"

    @pytest.mark.asyncio
    async def test_find_and_claim_dataset_success(self):
        """Test finding and claiming a dataset."""
        with patch('science_card_improvement.portal.status.get_settings'):
            workflow = CollaborativeWorkflow(user_id="test_user")

            with patch.object(PortalStatusManager, '__aenter__', new_callable=AsyncMock) as mock_enter:
                mock_manager = AsyncMock()
                mock_enter.return_value = mock_manager

                mock_manager.search_minimal_datasets.return_value = [
                    {"id": "minimal/dataset", "tags": ["biology"]}
                ]
                mock_manager.check_availability.return_value = {"available": True}
                mock_manager.get_dataset_metadata.return_value = {"category": "minimal"}
                mock_manager.claim_dataset.return_value = True

                with patch.object(PortalStatusManager, '__aexit__', new_callable=AsyncMock):
                    result = await workflow.find_and_claim_dataset()

                    assert result is not None
                    assert result["dataset_id"] == "minimal/dataset"

    @pytest.mark.asyncio
    async def test_update_progress(self):
        """Test updating progress."""
        with patch('science_card_improvement.portal.status.get_settings'):
            workflow = CollaborativeWorkflow(user_id="test_user")

            with patch.object(PortalStatusManager, '__aenter__', new_callable=AsyncMock) as mock_enter:
                mock_manager = AsyncMock()
                mock_enter.return_value = mock_manager
                mock_manager.update_status.return_value = True

                with patch.object(PortalStatusManager, '__aexit__', new_callable=AsyncMock):
                    result = await workflow.update_progress(
                        dataset_id="test/dataset",
                        status=WorkStatus.REVIEWING,
                        notes="Ready for review"
                    )

                    assert result is True

    @pytest.mark.asyncio
    async def test_complete_dataset(self):
        """Test completing dataset work."""
        with patch('science_card_improvement.portal.status.get_settings'):
            workflow = CollaborativeWorkflow(user_id="test_user")

            with patch.object(PortalStatusManager, '__aenter__', new_callable=AsyncMock) as mock_enter:
                mock_manager = AsyncMock()
                mock_enter.return_value = mock_manager
                mock_manager.complete_work.return_value = True

                with patch.object(PortalStatusManager, '__aexit__', new_callable=AsyncMock):
                    result = await workflow.complete_dataset(
                        dataset_id="test/dataset",
                        pr_url="https://github.com/pull/1",
                        before_score=40.0,
                        after_score=85.0,
                        improvements=["Added description"]
                    )

                    assert result is True
