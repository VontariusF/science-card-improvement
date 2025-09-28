"""Enhanced repository discovery with robust error handling and caching."""

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
from huggingface_hub import HfApi, DatasetInfo, ModelInfo
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from science_card_improvement.config.settings import get_settings
from science_card_improvement.exceptions.custom_exceptions import (
    AuthenticationError,
    NetworkError,
    RateLimitError,
    RepositoryNotFoundError,
)
from science_card_improvement.utils.cache import CacheManager
from science_card_improvement.utils.logger import LoggerMixin, RequestLogger, logger


@dataclass
class RepositoryMetadata:
    """Enhanced repository metadata with comprehensive information."""

    repo_id: str
    repo_type: str  # 'dataset' or 'model'
    title: str
    description: str
    tags: List[str] = field(default_factory=list)
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    downloads: int = 0
    likes: int = 0
    views: int = 0
    has_readme: bool = False
    readme_length: int = 0
    readme_quality_score: float = 0.0
    has_dataset_viewer: bool = False
    dataset_size: Optional[int] = None
    num_files: int = 0
    license: Optional[str] = None
    language: Optional[List[str]] = None
    task_categories: Optional[List[str]] = None
    card_data: Optional[Dict[str, Any]] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    priority_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            "repo_id": self.repo_id,
            "repo_type": self.repo_type,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "author": self.author,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "downloads": self.downloads,
            "likes": self.likes,
            "views": self.views,
            "has_readme": self.has_readme,
            "readme_length": self.readme_length,
            "readme_quality_score": self.readme_quality_score,
            "has_dataset_viewer": self.has_dataset_viewer,
            "dataset_size": self.dataset_size,
            "num_files": self.num_files,
            "license": self.license,
            "language": self.language,
            "task_categories": self.task_categories,
            "card_data": self.card_data,
            "metrics": self.metrics,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "priority_score": self.priority_score,
        }
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RepositoryMetadata":
        """Create instance from dictionary."""
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)

    def calculate_priority_score(self) -> float:
        """Calculate priority score for improvement based on multiple factors."""
        download_score = min(15.0, self.downloads / 500)
        like_score = min(10.0, self.likes / 10)
        view_score = min(5.0, self.views / 20000)
        popularity = download_score + like_score + view_score

        if not self.has_readme:
            documentation = 40.0
        elif self.readme_length < 300:
            documentation = 25.0
        elif self.readme_length < 1000:
            documentation = 15.0
        else:
            documentation = max(0.0, 10.0 - self.readme_quality_score * 10.0)

        completeness = 0.0
        if self.license is None or str(self.license).strip() == "":
            completeness += 5.0
        if not self.tags:
            completeness += 5.0
        if self.issues:
            completeness += min(10.0, len(self.issues) * 2.0)

        score = popularity + documentation + completeness
        self.priority_score = min(100.0, score)
        return self.priority_score


class RepositoryDiscovery(LoggerMixin):
    """Enhanced repository discovery with robust features."""

    def __init__(
        self,
        token: Optional[str] = None,
        cache_enabled: bool = True,
        parallel_workers: Optional[int] = None,
    ):
        """Initialize repository discovery.

        Args:
            token: Hugging Face API token
            cache_enabled: Enable caching for API responses
            parallel_workers: Number of parallel workers for API calls
        """
        self.settings = get_settings()
        self.api = HfApi(token=token or self.settings.hf_token.get_secret_value() if self.settings.hf_token else None)
        self.cache_manager = CacheManager() if cache_enabled else None
        self.parallel_workers = parallel_workers or self.settings.discovery_max_workers

        # Load configuration
        self.science_keywords = self._load_science_keywords()
        self.domain_tags = self._load_domain_tags()

        # Statistics tracking
        self.stats = {
            "total_discovered": 0,
            "total_processed": 0,
            "cache_hits": 0,
            "api_calls": 0,
            "errors": 0,
        }

    def _load_science_keywords(self) -> List[str]:
        """Load science keywords from configuration."""
        keywords_file = self.settings.config_dir / "science_keywords.json"
        if keywords_file.exists():
            with open(keywords_file, "r") as f:
                data = json.load(f)
            if isinstance(data, dict):
                keywords = data.get("keywords", [])
            elif isinstance(data, list):
                keywords = data
            else:
                keywords = []

            keywords = [kw for kw in keywords if isinstance(kw, str)]
            if keywords:
                return keywords

        # Default keywords
        return [
            "science", "biology", "genomics", "proteomics", "chemistry",
            "physics", "astronomy", "medicine", "medical", "clinical",
            "healthcare", "neuroscience", "ecology", "climate", "environmental",
            "computational-biology", "bioinformatics", "drug-discovery",
            "molecular", "genetics", "epidemiology", "pharmacology",
        ]

    def _load_domain_tags(self) -> Dict[str, List[str]]:
        """Load domain-specific tags from configuration."""
        tags_file = self.settings.config_dir / "domain_tags.json"
        if tags_file.exists():
            with open(tags_file, "r") as f:
                return json.load(f)
        else:
            # Default domain tags
            return {
                "biology": ["biology", "genomics", "proteomics", "single-cell", "bioinformatics"],
                "chemistry": ["chemistry", "molecular", "drug-discovery", "materials"],
                "physics": ["physics", "astronomy", "quantum", "particle-physics"],
                "medicine": ["medical", "clinical", "healthcare", "diagnostics"],
                "environment": ["climate", "ecology", "environmental", "earth-science"],
            }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((NetworkError, RateLimitError)),
    )
    async def discover_repositories(
        self,
        repo_type: str = "both",
        limit: int = 100,
        keywords: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "downloads",
        cache_ttl: Optional[int] = None,
    ) -> List[RepositoryMetadata]:
        """Discover repositories with advanced filtering and sorting.

        Args:
            repo_type: Type of repositories ('dataset', 'model', or 'both')
            limit: Maximum number of repositories to return
            keywords: Optional list of keywords to search (defaults to science keywords)
            filters: Optional filters (e.g., {'min_downloads': 100})
            sort_by: Sort criteria ('downloads', 'likes', 'updated', 'priority')
            cache_ttl: Cache TTL in seconds

        Returns:
            List of discovered repository metadata
        """
        with RequestLogger(self.logger, "repository_discovery", repo_type=repo_type, limit=limit):
            keywords = keywords or self.science_keywords
            cache_ttl = cache_ttl or self.settings.discovery_cache_ttl

            # Check cache
            cache_key = self._generate_cache_key(repo_type, keywords, filters)
            if self.cache_manager:
                cached_data = await self.cache_manager.get(cache_key)
                if cached_data:
                    self.stats["cache_hits"] += 1
                    self.log_info("Retrieved from cache", cache_key=cache_key)
                    return [RepositoryMetadata.from_dict(item) for item in cached_data]

            # Discover repositories
            repositories = []

            if repo_type in ["dataset", "both"]:
                datasets = await self._discover_datasets(keywords, limit // 2 if repo_type == "both" else limit)
                repositories.extend(datasets)

            if repo_type in ["model", "both"]:
                models = await self._discover_models(keywords, limit // 2 if repo_type == "both" else limit)
                repositories.extend(models)

            # Apply filters
            if filters:
                repositories = self._apply_filters(repositories, filters)

            # Enrich metadata in parallel
            repositories = await self._enrich_metadata_parallel(repositories)

            # Calculate priority scores
            for repo in repositories:
                repo.calculate_priority_score()

            # Sort repositories
            repositories = self._sort_repositories(repositories, sort_by)

            # Limit results
            repositories = repositories[:limit]

            # Cache results
            if self.cache_manager:
                cache_data = [repo.to_dict() for repo in repositories]
                await self.cache_manager.set(cache_key, cache_data, ttl=cache_ttl)

            # Update statistics
            self.stats["total_discovered"] += len(repositories)

            self.log_info(
                "Discovery completed",
                discovered=len(repositories),
                stats=self.stats,
            )

            return repositories

    async def _discover_datasets(self, keywords: List[str], limit: int) -> List[RepositoryMetadata]:
        """Discover datasets from Hugging Face with intelligent keyword handling."""
        datasets = []
        seen_ids = set()

        # Use minimum of 10 results per keyword to ensure good coverage
        # but cap at 100 to avoid too many API calls for large keyword lists
        per_keyword_limit = max(10, min(100, limit // max(1, len(keywords))))

        self.log_info(f"Searching with {len(keywords)} keywords, {per_keyword_limit} results per keyword")

        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = []

            for keyword in keywords:
                future = executor.submit(self._search_datasets_sync, keyword, per_keyword_limit)
                futures.append((keyword, future))

            for keyword, future in futures:
                try:
                    results = future.result(timeout=30)
                    for dataset_info in results:
                        if dataset_info.id not in seen_ids:
                            seen_ids.add(dataset_info.id)
                            metadata = self._convert_dataset_to_metadata(dataset_info)
                            if metadata:
                                datasets.append(metadata)

                            if len(datasets) >= limit:
                                break
                except Exception as e:
                    self.log_error(f"Error discovering datasets for '{keyword}'", exception=e)
                    self.stats["errors"] += 1

                if len(datasets) >= limit:
                    break

        return datasets[:limit]

    def _search_datasets_sync(self, keyword: str, limit: int) -> List[DatasetInfo]:
        """Synchronous dataset search for thread pool."""
        self.stats["api_calls"] += 1
        try:
            return list(self.api.list_datasets(
                search=keyword,
                limit=limit,
                full=True,
            ))
        except Exception as e:
            self.log_error(f"API error searching datasets", keyword=keyword, exception=e)
            return []

    async def _discover_models(self, keywords: List[str], limit: int) -> List[RepositoryMetadata]:
        """Discover models from Hugging Face with intelligent keyword handling."""
        models = []
        seen_ids = set()

        # Use minimum of 10 results per keyword to ensure good coverage
        # but cap at 100 to avoid too many API calls for large keyword lists
        per_keyword_limit = max(10, min(100, limit // max(1, len(keywords))))

        self.log_info(f"Searching with {len(keywords)} keywords, {per_keyword_limit} results per keyword")

        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = []

            for keyword in keywords:
                future = executor.submit(self._search_models_sync, keyword, per_keyword_limit)
                futures.append((keyword, future))

            for keyword, future in futures:
                try:
                    results = future.result(timeout=30)
                    for model_info in results:
                        if model_info.id not in seen_ids:
                            seen_ids.add(model_info.id)
                            metadata = self._convert_model_to_metadata(model_info)
                            if metadata:
                                models.append(metadata)

                            if len(models) >= limit:
                                break
                except Exception as e:
                    self.log_error(f"Error discovering models for '{keyword}'", exception=e)
                    self.stats["errors"] += 1

                if len(models) >= limit:
                    break

        return models[:limit]

    def _search_models_sync(self, keyword: str, limit: int) -> List[ModelInfo]:
        """Synchronous model search for thread pool."""
        self.stats["api_calls"] += 1
        try:
            return list(self.api.list_models(
                search=keyword,
                limit=limit,
                full=True,
            ))
        except Exception as e:
            self.log_error(f"API error searching models", keyword=keyword, exception=e)
            return []

    def _convert_dataset_to_metadata(self, dataset_info: DatasetInfo) -> Optional[RepositoryMetadata]:
        """Convert DatasetInfo to RepositoryMetadata."""
        try:
            return RepositoryMetadata(
                repo_id=dataset_info.id,
                repo_type="dataset",
                title=getattr(dataset_info, "cardData", {}).get("pretty_name", dataset_info.id),
                description=getattr(dataset_info, "description", ""),
                tags=getattr(dataset_info, "tags", []),
                author=dataset_info.id.split("/")[0] if "/" in dataset_info.id else None,
                created_at=getattr(dataset_info, "created_at", None),
                updated_at=getattr(dataset_info, "lastModified", None),
                downloads=getattr(dataset_info, "downloads", 0),
                likes=getattr(dataset_info, "likes", 0),
                license=getattr(dataset_info, "cardData", {}).get("license"),
                task_categories=getattr(dataset_info, "cardData", {}).get("task_categories"),
                language=getattr(dataset_info, "cardData", {}).get("language"),
                card_data=getattr(dataset_info, "cardData", {}),
            )
        except Exception as e:
            self.log_error(f"Error converting dataset {dataset_info.id}", exception=e)
            return None

    def _convert_model_to_metadata(self, model_info: ModelInfo) -> Optional[RepositoryMetadata]:
        """Convert ModelInfo to RepositoryMetadata."""
        try:
            return RepositoryMetadata(
                repo_id=model_info.id,
                repo_type="model",
                title=getattr(model_info, "cardData", {}).get("model_name", model_info.id),
                description=getattr(model_info, "description", ""),
                tags=getattr(model_info, "tags", []),
                author=model_info.id.split("/")[0] if "/" in model_info.id else None,
                created_at=getattr(model_info, "created_at", None),
                updated_at=getattr(model_info, "lastModified", None),
                downloads=getattr(model_info, "downloads", 0),
                likes=getattr(model_info, "likes", 0),
                license=getattr(model_info, "cardData", {}).get("license"),
                task_categories=getattr(model_info, "pipeline_tag", []),
                language=getattr(model_info, "cardData", {}).get("language"),
                card_data=getattr(model_info, "cardData", {}),
            )
        except Exception as e:
            self.log_error(f"Error converting model {model_info.id}", exception=e)
            return None

    async def _enrich_metadata_parallel(self, repositories: List[RepositoryMetadata]) -> List[RepositoryMetadata]:
        """Enrich repository metadata in parallel."""
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = {
                executor.submit(self._enrich_single_repository, repo): repo
                for repo in repositories
            }

            enriched_repos = []
            for future in as_completed(futures):
                try:
                    repo = future.result(timeout=10)
                    if repo:
                        enriched_repos.append(repo)
                        self.stats["total_processed"] += 1
                except Exception as e:
                    self.log_error("Error enriching repository", exception=e)
                    self.stats["errors"] += 1
                    # Keep original repository even if enrichment fails
                    enriched_repos.append(futures[future])

        return enriched_repos

    def _enrich_single_repository(self, repo: RepositoryMetadata) -> RepositoryMetadata:
        """Enrich a single repository with additional metadata."""
        try:
            # Check for README
            try:
                readme_path = self.api.hf_hub_download(
                    repo_id=repo.repo_id,
                    filename="README.md",
                    repo_type=repo.repo_type,
                )
                with open(readme_path, "r", encoding="utf-8") as f:
                    readme_content = f.read()
                    repo.has_readme = True
                    repo.readme_length = len(readme_content)

                    # Basic quality assessment
                    repo.readme_quality_score = self._assess_readme_quality(readme_content)

                    # Identify issues
                    repo.issues = self._identify_readme_issues(readme_content)

                    # Generate suggestions
                    repo.suggestions = self._generate_suggestions(repo)
            except Exception:
                repo.has_readme = False
                repo.issues.append("Missing README.md file")
                repo.suggestions.append("Create a comprehensive README.md file")

            # Get repository files
            try:
                files = self.api.list_repo_files(
                    repo_id=repo.repo_id,
                    repo_type=repo.repo_type,
                )
                repo.num_files = len(files)
            except Exception:
                pass

            return repo

        except Exception as e:
            self.log_error(f"Error enriching repository {repo.repo_id}", exception=e)
            return repo

    def _assess_readme_quality(self, content: str) -> float:
        """Assess README quality (0-1 score)."""
        score = 0.0
        max_score = 10.0

        # Check length
        if len(content) > 1000:
            score += 2.0
        elif len(content) > 500:
            score += 1.0

        # Check for important sections
        important_sections = [
            "description", "installation", "usage", "data", "license",
            "citation", "authors", "acknowledgments", "references"
        ]

        content_lower = content.lower()
        for section in important_sections:
            if section in content_lower:
                score += 1.0

        return min(1.0, score / max_score)

    def _identify_readme_issues(self, content: str) -> List[str]:
        """Identify issues in README content."""
        issues = []
        content_lower = content.lower()

        if len(content) < 300:
            issues.append("README is too short (less than 300 characters)")

        required_sections = ["license", "citation"]
        for section in required_sections:
            if section not in content_lower:
                issues.append(f"Missing {section} section")

        if "```" not in content:
            issues.append("No code examples provided")

        if not any(word in content_lower for word in ["install", "setup", "getting started"]):
            issues.append("Missing installation or setup instructions")

        return issues

    def _generate_suggestions(self, repo: RepositoryMetadata) -> List[str]:
        """Generate improvement suggestions for a repository."""
        suggestions = []

        if not repo.has_readme:
            suggestions.append("Create a comprehensive README.md file")
            return suggestions

        if repo.readme_length < 300:
            suggestions.append("Expand README with more detailed information")

        if not repo.license:
            suggestions.append("Add license information")

        if not repo.tags or len(repo.tags) < 3:
            suggestions.append("Add more descriptive tags")

        if repo.repo_type == "dataset" and "data" not in repo.description.lower():
            suggestions.append("Add dataset structure and schema information")

        if repo.repo_type == "model" and "training" not in repo.description.lower():
            suggestions.append("Add training details and hyperparameters")

        return suggestions

    def _apply_filters(
        self,
        repositories: List[RepositoryMetadata],
        filters: Dict[str, Any]
    ) -> List[RepositoryMetadata]:
        """Apply filters to repository list."""
        filtered = repositories

        if "min_downloads" in filters:
            filtered = [r for r in filtered if r.downloads >= filters["min_downloads"]]

        if "min_likes" in filters:
            filtered = [r for r in filtered if r.likes >= filters["min_likes"]]

        if "has_readme" in filters:
            filtered = [r for r in filtered if r.has_readme == filters["has_readme"]]

        if "max_readme_length" in filters:
            filtered = [r for r in filtered if r.readme_length <= filters["max_readme_length"]]

        if "needs_improvement" in filters and filters["needs_improvement"]:
            filtered = [r for r in filtered if r.issues or r.readme_quality_score < 0.5]

        return filtered

    def _sort_repositories(
        self,
        repositories: List[RepositoryMetadata],
        sort_by: str
    ) -> List[RepositoryMetadata]:
        """Sort repositories by specified criteria."""
        if sort_by == "downloads":
            return sorted(repositories, key=lambda r: r.downloads, reverse=True)
        elif sort_by == "likes":
            return sorted(repositories, key=lambda r: r.likes, reverse=True)
        elif sort_by == "updated":
            return sorted(
                repositories,
                key=lambda r: r.updated_at if r.updated_at else datetime.min,
                reverse=True
            )
        elif sort_by == "priority":
            return sorted(repositories, key=lambda r: r.priority_score, reverse=True)
        elif sort_by == "readme_quality":
            return sorted(repositories, key=lambda r: r.readme_quality_score, reverse=True)
        else:
            return repositories

    def _generate_cache_key(
        self,
        repo_type: str,
        keywords: List[str],
        filters: Optional[Dict[str, Any]]
    ) -> str:
        """Generate cache key for discovery results."""
        key_parts = [
            "discovery",
            repo_type,
            "-".join(sorted(keywords[:5])),  # Limit keywords for key
        ]

        if filters:
            filter_str = "-".join(f"{k}_{v}" for k, v in sorted(filters.items()))
            key_parts.append(filter_str)

        return ":".join(key_parts)

    async def export_results(
        self,
        repositories: List[RepositoryMetadata],
        output_file: Path,
        format: str = "json"
    ) -> None:
        """Export discovery results to file.

        Args:
            repositories: List of repositories to export
            output_file: Output file path
            format: Export format ('json', 'csv', 'excel')
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            data = [repo.to_dict() for repo in repositories]
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2, default=str)

        elif format == "csv":
            df = pd.DataFrame([repo.to_dict() for repo in repositories])
            df.to_csv(output_file, index=False)

        elif format == "excel":
            df = pd.DataFrame([repo.to_dict() for repo in repositories])
            with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Repositories", index=False)

                # Add summary sheet
                summary_df = self._create_summary_dataframe(repositories)
                summary_df.to_excel(writer, sheet_name="Summary", index=False)

        self.log_info(f"Exported {len(repositories)} repositories to {output_file}")

    def _create_summary_dataframe(self, repositories: List[RepositoryMetadata]) -> pd.DataFrame:
        """Create summary statistics dataframe."""
        summary = {
            "Total Repositories": len(repositories),
            "Datasets": sum(1 for r in repositories if r.repo_type == "dataset"),
            "Models": sum(1 for r in repositories if r.repo_type == "model"),
            "Missing README": sum(1 for r in repositories if not r.has_readme),
            "Short README (<300)": sum(1 for r in repositories if r.has_readme and r.readme_length < 300),
            "Average Downloads": sum(r.downloads for r in repositories) / len(repositories) if repositories else 0,
            "Average Likes": sum(r.likes for r in repositories) / len(repositories) if repositories else 0,
            "Need Improvement": sum(1 for r in repositories if r.priority_score > 50),
        }

        return pd.DataFrame([summary])

    def get_statistics(self) -> Dict[str, Any]:
        """Get discovery statistics."""
        return self.stats.copy()