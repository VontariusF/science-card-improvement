"""Status management integration with the improved Hugging Science Portal."""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp
from gradio_client import Client

from science_card_improvement.config.settings import get_settings
from science_card_improvement.utils.logger import LoggerMixin


class WorkStatus(Enum):
    """Status options for dataset card work."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    NEEDS_HELP = "needs_help"
    BLOCKED = "blocked"


@dataclass
class DatasetWorkStatus:
    """Work status for a dataset card improvement."""

    dataset_id: str
    user_id: str
    status: WorkStatus
    started_at: Optional[datetime] = None
    last_updated: datetime = None
    notes: str = ""
    estimated_completion: Optional[datetime] = None
    pr_url: Optional[str] = None
    improvement_score: Optional[float] = None


class PortalStatusManager(LoggerMixin):
    """Manages work status updates with the Hugging Science Portal."""

    PORTAL_URL = "https://huggingface.co/spaces/hugging-science/dataset-insight-portal"
    API_ENDPOINT = "https://hugging-science-dataset-insight-portal.hf.space"

    def __init__(self, user_id: Optional[str] = None):
        """Initialize status manager.

        Args:
            user_id: Your Hugging Face user ID for status tracking
        """
        self.settings = get_settings()
        self.user_id = user_id or self.settings.hf_username
        self.client = None
        self._session = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession()
        try:
            self.client = Client(self.API_ENDPOINT)
            self.log_info(f"Connected to portal as {self.user_id}")
        except Exception as e:
            self.log_warning(f"Could not connect to portal: {e}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()

    async def claim_dataset(
        self,
        dataset_id: str,
        notes: str = "",
        estimated_days: int = 3
    ) -> bool:
        """Claim a dataset to work on.

        Args:
            dataset_id: Dataset repository ID
            notes: Optional notes about planned improvements
            estimated_days: Estimated days to completion

        Returns:
            Whether the claim was successful
        """
        try:
            status_data = {
                "dataset_id": dataset_id,
                "user_id": self.user_id,
                "status": WorkStatus.IN_PROGRESS.value,
                "started_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "notes": notes or f"Working on improving documentation",
                "estimated_completion": (
                    datetime.utcnow() + timedelta(days=estimated_days)
                ).isoformat()
            }

            if self.client:
                result = self.client.predict(
                    fn_index=6,  # update_status function
                    **status_data
                )
                success = result.get("success", False)
            else:
                success = await self._http_update_status(status_data)

            if success:
                self.log_info(f"Successfully claimed {dataset_id}")
            else:
                self.log_warning(f"Could not claim {dataset_id} - may already be taken")

            return success

        except Exception as e:
            self.log_error(f"Error claiming dataset: {e}")
            return False

    async def update_status(
        self,
        dataset_id: str,
        status: WorkStatus,
        notes: Optional[str] = None,
        pr_url: Optional[str] = None
    ) -> bool:
        """Update work status for a dataset.

        Args:
            dataset_id: Dataset repository ID
            status: New work status
            notes: Optional status notes
            pr_url: Optional PR URL if completed

        Returns:
            Whether the update was successful
        """
        try:
            status_data = {
                "dataset_id": dataset_id,
                "user_id": self.user_id,
                "status": status.value,
                "last_updated": datetime.utcnow().isoformat(),
            }

            if notes:
                status_data["notes"] = notes
            if pr_url:
                status_data["pr_url"] = pr_url

            if self.client:
                result = self.client.predict(
                    fn_index=6,  # update_status function
                    **status_data
                )
                return result.get("success", False)
            else:
                return await self._http_update_status(status_data)

        except Exception as e:
            self.log_error(f"Error updating status: {e}")
            return False

    async def check_availability(self, dataset_id: str) -> Dict[str, Any]:
        """Check if a dataset is available to work on.

        Args:
            dataset_id: Dataset repository ID

        Returns:
            Status information including:
            - available: Whether dataset is available
            - current_worker: User currently working on it (if any)
            - status: Current work status
            - last_updated: When status was last updated
        """
        try:
            if self.client:
                result = self.client.predict(
                    fn_index=7,  # check_status function
                    dataset_id=dataset_id
                )
                return result
            else:
                return await self._http_check_status(dataset_id)

        except Exception as e:
            self.log_error(f"Error checking availability: {e}")
            return {
                "available": True,  # Assume available if check fails
                "current_worker": None,
                "status": "unknown"
            }

    async def get_my_datasets(self) -> List[Dict[str, Any]]:
        """Get all datasets the current user is working on.

        Returns:
            List of datasets with status information
        """
        try:
            if self.client:
                result = self.client.predict(
                    fn_index=8,  # get_user_datasets function
                    user_id=self.user_id
                )
                return result
            else:
                return await self._http_get_user_datasets(self.user_id)

        except Exception as e:
            self.log_error(f"Error getting user datasets: {e}")
            return []

    async def search_minimal_datasets(
        self,
        limit: int = 50,
        exclude_claimed: bool = True
    ) -> List[Dict[str, Any]]:
        """Search for minimal documentation datasets.

        Args:
            limit: Maximum number of results
            exclude_claimed: Exclude datasets already claimed by others

        Returns:
            List of minimal documentation datasets with metadata
        """
        try:
            params = {
                "category": "minimal",
                "limit": limit,
                "exclude_claimed": exclude_claimed
            }

            if self.client:
                result = self.client.predict(
                    fn_index=0,  # search_datasets function
                    **params
                )
                return result
            else:
                return await self._http_search_minimal(params)

        except Exception as e:
            self.log_error(f"Error searching minimal datasets: {e}")
            return []

    async def get_dataset_metadata(self, dataset_id: str) -> Dict[str, Any]:
        """Get enriched metadata for a dataset.

        Args:
            dataset_id: Dataset repository ID

        Returns:
            Metadata including:
            - number_of_downloads
            - storage_size
            - last_modified
            - current_status
            - documentation_score
        """
        try:
            if self.client:
                result = self.client.predict(
                    fn_index=9,  # get_metadata function
                    dataset_id=dataset_id
                )
                return result
            else:
                return await self._http_get_metadata(dataset_id)

        except Exception as e:
            self.log_error(f"Error getting metadata: {e}")
            return {}

    async def complete_work(
        self,
        dataset_id: str,
        pr_url: str,
        before_score: float,
        after_score: float,
        improvements: List[str]
    ) -> bool:
        """Mark dataset work as completed with results.

        Args:
            dataset_id: Dataset repository ID
            pr_url: Pull request URL
            before_score: Documentation score before
            after_score: Documentation score after
            improvements: List of improvements made

        Returns:
            Whether the completion was recorded successfully
        """
        try:
            completion_data = {
                "dataset_id": dataset_id,
                "user_id": self.user_id,
                "status": WorkStatus.COMPLETED.value,
                "pr_url": pr_url,
                "improvement_score": after_score - before_score,
                "notes": f"Completed. Score: {before_score:.1f} → {after_score:.1f}. "
                        f"Improvements: {', '.join(improvements[:3])}",
                "completed_at": datetime.utcnow().isoformat()
            }

            if self.client:
                result = self.client.predict(
                    fn_index=10,  # complete_work function
                    **completion_data
                )
                return result.get("success", False)
            else:
                return await self._http_complete_work(completion_data)

        except Exception as e:
            self.log_error(f"Error completing work: {e}")
            return False

    # HTTP fallback methods
    async def _http_update_status(self, data: Dict[str, Any]) -> bool:
        """HTTP fallback for status updates."""
        if not self._session:
            return False

        url = f"{self.API_ENDPOINT}/api/status/update"
        async with self._session.post(url, json=data) as response:
            return response.status == 200

    async def _http_check_status(self, dataset_id: str) -> Dict[str, Any]:
        """HTTP fallback for status check."""
        if not self._session:
            return {"available": True}

        url = f"{self.API_ENDPOINT}/api/status/{dataset_id}"
        async with self._session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return {"available": True}

    async def _http_get_user_datasets(self, user_id: str) -> List[Dict[str, Any]]:
        """HTTP fallback for user datasets."""
        if not self._session:
            return []

        url = f"{self.API_ENDPOINT}/api/user/{user_id}/datasets"
        async with self._session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return []

    async def _http_search_minimal(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """HTTP fallback for minimal dataset search."""
        if not self._session:
            return []

        from urllib.parse import urlencode
        url = f"{self.API_ENDPOINT}/api/search/minimal?{urlencode(params)}"
        async with self._session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return []

    async def _http_get_metadata(self, dataset_id: str) -> Dict[str, Any]:
        """HTTP fallback for metadata retrieval."""
        if not self._session:
            return {}

        url = f"{self.API_ENDPOINT}/api/metadata/{dataset_id}"
        async with self._session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return {}

    async def _http_complete_work(self, data: Dict[str, Any]) -> bool:
        """HTTP fallback for work completion."""
        if not self._session:
            return False

        url = f"{self.API_ENDPOINT}/api/status/complete"
        async with self._session.post(url, json=data) as response:
            return response.status == 200


from datetime import timedelta


class CollaborativeWorkflow(LoggerMixin):
    """Collaborative workflow using portal status tracking."""

    def __init__(self, user_id: str):
        """Initialize collaborative workflow.

        Args:
            user_id: Your Hugging Face user ID
        """
        self.user_id = user_id
        self.settings = get_settings()

    async def find_and_claim_dataset(
        self,
        category: str = "minimal",
        preferred_domains: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Find and claim an available dataset to work on.

        Args:
            category: Category to search (minimal, low_quality, etc.)
            preferred_domains: Preferred scientific domains

        Returns:
            Claimed dataset information or None if nothing available
        """
        async with PortalStatusManager(self.user_id) as manager:
            # Search for minimal datasets
            datasets = await manager.search_minimal_datasets(
                limit=100,
                exclude_claimed=True
            )

            # Filter by preferred domains if specified
            if preferred_domains:
                filtered = [
                    d for d in datasets
                    if any(domain in d.get("tags", []) for domain in preferred_domains)
                ]
                if filtered:
                    datasets = filtered

            # Try to claim the first available dataset
            for dataset in datasets:
                dataset_id = dataset.get("id")

                # Double-check availability
                status_info = await manager.check_availability(dataset_id)
                if status_info.get("available"):
                    # Get full metadata
                    metadata = await manager.get_dataset_metadata(dataset_id)

                    # Claim it
                    success = await manager.claim_dataset(
                        dataset_id=dataset_id,
                        notes=f"Improving documentation - targeting {metadata.get('category', 'minimal')} category",
                        estimated_days=3
                    )

                    if success:
                        self.log_info(f"Successfully claimed {dataset_id}")
                        return {
                            "dataset_id": dataset_id,
                            "metadata": metadata,
                            "status": "claimed"
                        }

            self.log_warning("No available datasets found to claim")
            return None

    async def update_progress(
        self,
        dataset_id: str,
        status: WorkStatus,
        notes: str = ""
    ) -> bool:
        """Update progress on a dataset.

        Args:
            dataset_id: Dataset being worked on
            status: Current status
            notes: Progress notes

        Returns:
            Whether update was successful
        """
        async with PortalStatusManager(self.user_id) as manager:
            return await manager.update_status(
                dataset_id=dataset_id,
                status=status,
                notes=notes
            )

    async def complete_dataset(
        self,
        dataset_id: str,
        pr_url: str,
        before_score: float,
        after_score: float,
        improvements: List[str]
    ) -> bool:
        """Mark a dataset as completed with results.

        Args:
            dataset_id: Dataset that was improved
            pr_url: PR with improvements
            before_score: Score before improvements
            after_score: Score after improvements
            improvements: List of improvements made

        Returns:
            Whether completion was recorded
        """
        async with PortalStatusManager(self.user_id) as manager:
            return await manager.complete_work(
                dataset_id=dataset_id,
                pr_url=pr_url,
                before_score=before_score,
                after_score=after_score,
                improvements=improvements
            )