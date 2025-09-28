"""Integration with Hugging Science Dataset Insight Portal for enhanced discovery and quality assessment."""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import aiohttp
from gradio_client import Client

from science_card_improvement.config.settings import get_settings
from science_card_improvement.exceptions.custom_exceptions import NetworkError
from science_card_improvement.utils.logger import LoggerMixin


@dataclass
class PortalDatasetInsight:
    """Dataset insight from the Hugging Science portal."""

    repo_id: str
    category: str  # genomics, medical, chemistry, etc.
    quality_metrics: Dict[str, Any]
    documentation_score: float
    usage_stats: Dict[str, int]
    community_engagement: Dict[str, Any]
    improvement_priority: float
    last_updated: datetime
    scientific_impact: Dict[str, Any] = field(default_factory=dict)
    missing_components: List[str] = field(default_factory=list)
    recommended_tags: List[str] = field(default_factory=list)


class HuggingSciencePortal(LoggerMixin):
    """Interface to the Hugging Science Dataset Insight Portal."""

    PORTAL_URL = "https://huggingface.co/spaces/hugging-science/dataset-insight-portal"
    API_ENDPOINT = "https://hugging-science-dataset-insight-portal.hf.space"

    # Scientific categories from the portal
    SCIENCE_CATEGORIES = [
        "genomics",
        "proteomics",
        "medical_imaging",
        "clinical_data",
        "drug_discovery",
        "neuroscience",
        "chemistry",
        "biology",
        "physics",
        "earth_science",
        "environmental",
        "materials_science"
    ]

    def __init__(self, cache_enabled: bool = True):
        """Initialize portal integration.

        Args:
            cache_enabled: Whether to cache portal responses
        """
        self.settings = get_settings()
        self.cache_enabled = cache_enabled
        self.client = None
        self._session = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession()
        try:
            # Initialize Gradio client for Space interaction
            self.client = Client(self.API_ENDPOINT)
            self.log_info("Connected to Hugging Science Portal")
        except Exception as e:
            self.log_warning(f"Could not connect to portal directly: {e}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()

    async def search_science_datasets(
        self,
        category: Optional[str] = None,
        min_quality_score: float = 0,
        max_quality_score: float = 100,
        limit: int = 100,
        sort_by: str = "improvement_priority"
    ) -> List[PortalDatasetInsight]:
        """Search for science datasets using portal insights.

        Args:
            category: Scientific category to filter by
            min_quality_score: Minimum documentation quality score
            max_quality_score: Maximum documentation quality score
            limit: Maximum number of results
            sort_by: Sort criteria (improvement_priority, quality_score, usage)

        Returns:
            List of dataset insights from the portal
        """
        insights = []

        try:
            # Query the portal's dataset database
            params = {
                "category": category or "all",
                "min_score": min_quality_score,
                "max_score": max_quality_score,
                "limit": limit,
                "sort": sort_by
            }

            if self.client:
                # Use Gradio API if available
                result = self.client.predict(
                    fn_index=0,  # search_datasets function
                    **params
                )
                datasets = json.loads(result)
            else:
                # Fallback to HTTP API
                datasets = await self._http_search(params)

            # Convert to insights
            for dataset in datasets:
                insight = self._parse_dataset_insight(dataset)
                if insight:
                    insights.append(insight)

            self.log_info(f"Retrieved {len(insights)} dataset insights from portal")

        except Exception as e:
            self.log_error(f"Portal search failed: {e}")
            # Fallback to our own discovery if portal is unavailable
            insights = []

        return insights

    async def get_dataset_quality_report(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed quality report for a specific dataset.

        Args:
            repo_id: Repository ID to analyze

        Returns:
            Detailed quality report from the portal
        """
        try:
            if self.client:
                # Use Gradio API for detailed analysis
                report = self.client.predict(
                    fn_index=1,  # analyze_dataset function
                    repo_id=repo_id
                )
                return json.loads(report)
            else:
                # HTTP fallback
                return await self._http_get_report(repo_id)

        except Exception as e:
            self.log_error(f"Could not get quality report for {repo_id}: {e}")
            return None

    async def get_improvement_recommendations(
        self,
        repo_id: str
    ) -> Dict[str, Any]:
        """Get specific improvement recommendations from the portal.

        Args:
            repo_id: Repository to get recommendations for

        Returns:
            Structured recommendations including:
            - Missing documentation sections
            - Quality improvement suggestions
            - Best practice examples
            - Similar high-quality datasets
        """
        try:
            if self.client:
                recommendations = self.client.predict(
                    fn_index=2,  # get_recommendations function
                    repo_id=repo_id
                )
                return json.loads(recommendations)
            else:
                return await self._http_get_recommendations(repo_id)

        except Exception as e:
            self.log_error(f"Could not get recommendations for {repo_id}: {e}")
            return {
                "recommendations": [],
                "similar_quality_datasets": [],
                "improvement_score_potential": 0
            }

    async def get_trending_science_datasets(
        self,
        timeframe: str = "week",
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get trending science datasets from the portal.

        Args:
            timeframe: Time period (day, week, month)
            category: Optional scientific category filter

        Returns:
            List of trending datasets with engagement metrics
        """
        try:
            if self.client:
                trending = self.client.predict(
                    fn_index=3,  # get_trending function
                    timeframe=timeframe,
                    category=category or "all"
                )
                return json.loads(trending)
            else:
                return await self._http_get_trending(timeframe, category)

        except Exception as e:
            self.log_error(f"Could not get trending datasets: {e}")
            return []

    async def submit_improvement_result(
        self,
        repo_id: str,
        before_score: float,
        after_score: float,
        improvements_made: List[str]
    ) -> bool:
        """Submit improvement results back to the portal for tracking.

        Args:
            repo_id: Repository that was improved
            before_score: Documentation score before improvements
            after_score: Documentation score after improvements
            improvements_made: List of improvements implemented

        Returns:
            Whether submission was successful
        """
        try:
            data = {
                "repo_id": repo_id,
                "before_score": before_score,
                "after_score": after_score,
                "improvement_delta": after_score - before_score,
                "improvements": improvements_made,
                "timestamp": datetime.utcnow().isoformat(),
                "tool": "Science Card Improvement Toolkit"
            }

            if self.client:
                result = self.client.predict(
                    fn_index=4,  # submit_improvement function
                    **data
                )
                return result.get("success", False)
            else:
                return await self._http_submit_improvement(data)

        except Exception as e:
            self.log_error(f"Could not submit improvement result: {e}")
            return False

    async def get_community_insights(self, repo_id: str) -> Dict[str, Any]:
        """Get community engagement insights for a dataset.

        Args:
            repo_id: Repository to analyze

        Returns:
            Community metrics including:
            - Download trends
            - Usage in papers/projects
            - Community discussions
            - Fork statistics
        """
        try:
            if self.client:
                insights = self.client.predict(
                    fn_index=5,  # get_community_insights function
                    repo_id=repo_id
                )
                return json.loads(insights)
            else:
                return await self._http_get_community_insights(repo_id)

        except Exception as e:
            self.log_error(f"Could not get community insights: {e}")
            return {}

    def _parse_dataset_insight(self, data: Dict[str, Any]) -> Optional[PortalDatasetInsight]:
        """Parse raw portal data into dataset insight."""
        try:
            return PortalDatasetInsight(
                repo_id=data.get("id", ""),
                category=data.get("category", "unknown"),
                quality_metrics=data.get("quality_metrics", {}),
                documentation_score=data.get("doc_score", 0.0),
                usage_stats=data.get("usage", {}),
                community_engagement=data.get("community", {}),
                improvement_priority=data.get("priority", 0.0),
                last_updated=datetime.fromisoformat(
                    data.get("updated", datetime.utcnow().isoformat())
                ),
                scientific_impact=data.get("impact", {}),
                missing_components=data.get("missing", []),
                recommended_tags=data.get("tags", [])
            )
        except Exception as e:
            self.log_error(f"Could not parse dataset insight: {e}")
            return None

    # HTTP fallback methods
    async def _http_search(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """HTTP fallback for dataset search."""
        if not self._session:
            raise NetworkError("HTTP session not initialized")

        url = f"{self.API_ENDPOINT}/api/search?{urlencode(params)}"
        async with self._session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return []

    async def _http_get_report(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """HTTP fallback for quality report."""
        if not self._session:
            raise NetworkError("HTTP session not initialized")

        url = f"{self.API_ENDPOINT}/api/report/{repo_id}"
        async with self._session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return None

    async def _http_get_recommendations(self, repo_id: str) -> Dict[str, Any]:
        """HTTP fallback for recommendations."""
        if not self._session:
            raise NetworkError("HTTP session not initialized")

        url = f"{self.API_ENDPOINT}/api/recommendations/{repo_id}"
        async with self._session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return {"recommendations": []}

    async def _http_get_trending(
        self,
        timeframe: str,
        category: Optional[str]
    ) -> List[Dict[str, Any]]:
        """HTTP fallback for trending datasets."""
        if not self._session:
            raise NetworkError("HTTP session not initialized")

        params = {"timeframe": timeframe}
        if category:
            params["category"] = category

        url = f"{self.API_ENDPOINT}/api/trending?{urlencode(params)}"
        async with self._session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return []

    async def _http_submit_improvement(self, data: Dict[str, Any]) -> bool:
        """HTTP fallback for submitting improvements."""
        if not self._session:
            raise NetworkError("HTTP session not initialized")

        url = f"{self.API_ENDPOINT}/api/improvements"
        async with self._session.post(url, json=data) as response:
            return response.status == 200

    async def _http_get_community_insights(self, repo_id: str) -> Dict[str, Any]:
        """HTTP fallback for community insights."""
        if not self._session:
            raise NetworkError("HTTP session not initialized")

        url = f"{self.API_ENDPOINT}/api/community/{repo_id}"
        async with self._session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return {}


class EnhancedDiscoveryWithPortal(LoggerMixin):
    """Enhanced discovery combining our system with portal insights."""

    def __init__(self):
        """Initialize enhanced discovery."""
        self.settings = get_settings()

    async def discover_with_insights(
        self,
        limit: int = 200,
        categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Discover datasets using both our system and portal insights.

        Args:
            limit: Maximum datasets to discover
            categories: Scientific categories to focus on

        Returns:
            Combined and prioritized dataset list with insights
        """
        from science_card_improvement.discovery.repository import RepositoryDiscovery

        results = []

        # Get portal insights
        async with HuggingSciencePortal() as portal:
            # Get high-priority datasets from portal
            portal_insights = await portal.search_science_datasets(
                category=categories[0] if categories else None,
                max_quality_score=30,  # Focus on those needing improvement
                limit=limit // 2,
                sort_by="improvement_priority"
            )

            # Get trending datasets that need improvement
            trending = await portal.get_trending_science_datasets(
                timeframe="week",
                category=categories[0] if categories else None
            )

            # Our traditional discovery
            discovery = RepositoryDiscovery(cache_enabled=False)
            our_datasets = await discovery.discover_repositories(
                repo_type="dataset",
                limit=limit // 2
            )

            # Merge and enrich results
            seen_ids = set()

            # Add portal insights first (higher priority)
            for insight in portal_insights:
                if insight.repo_id not in seen_ids:
                    # Get additional recommendations
                    recommendations = await portal.get_improvement_recommendations(
                        insight.repo_id
                    )

                    results.append({
                        "repo_id": insight.repo_id,
                        "source": "portal",
                        "category": insight.category,
                        "documentation_score": insight.documentation_score,
                        "improvement_priority": insight.improvement_priority,
                        "missing_components": insight.missing_components,
                        "recommendations": recommendations,
                        "community_engagement": insight.community_engagement,
                        "is_trending": insight.repo_id in [t["id"] for t in trending]
                    })
                    seen_ids.add(insight.repo_id)

            # Add our discoveries
            for dataset in our_datasets:
                if dataset.repo_id not in seen_ids:
                    # Get portal insights if available
                    quality_report = await portal.get_dataset_quality_report(
                        dataset.repo_id
                    )

                    results.append({
                        "repo_id": dataset.repo_id,
                        "source": "traditional",
                        "documentation_score": dataset.readme_quality_score,
                        "improvement_priority": dataset.priority_score,
                        "quality_report": quality_report,
                        "has_readme": dataset.has_readme,
                        "readme_length": dataset.readme_length
                    })
                    seen_ids.add(dataset.repo_id)

        # Sort by improvement priority
        results.sort(key=lambda x: x.get("improvement_priority", 0), reverse=True)

        self.log_info(f"Discovered {len(results)} datasets with portal insights")
        return results[:limit]