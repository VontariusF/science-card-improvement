"""Unit tests for human review module."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from science_card_improvement.review.human import (
    ChangeProposal,
    HumanReviewSystem,
)
from science_card_improvement.discovery.repository import RepositoryMetadata


@pytest.mark.unit
class TestChangeProposal:
    """Test ChangeProposal dataclass."""

    def test_creation(self):
        """Test change proposal creation."""
        proposal = ChangeProposal(
            repo_id="user/dataset",
            original_content="# Old\n\nOld content",
            proposed_content="# New\n\nNew content",
            changes_made=["Added license", "Added citation"],
            priority_score=8.5,
            created_at=datetime.now(),
        )
        assert proposal.repo_id == "user/dataset"
        assert len(proposal.changes_made) == 2
        assert proposal.priority_score == 8.5

    def test_default_status(self):
        """Test default status."""
        proposal = ChangeProposal(
            repo_id="user/dataset",
            original_content="Original",
            proposed_content="New",
            changes_made=[],
            priority_score=5.0,
            created_at=datetime.now(),
        )
        assert proposal.status == "pending"


@pytest.mark.unit
class TestHumanReviewSystem:
    """Test HumanReviewSystem class."""

    @pytest.fixture
    def review_system(self):
        """Create review system instance."""
        return HumanReviewSystem()

    @pytest.fixture
    def sample_proposal(self):
        """Create sample change proposal."""
        return ChangeProposal(
            repo_id="user/dataset",
            original_content="# Old Content",
            proposed_content="# New Content\n\n## Description\nImproved",
            changes_made=["Added description section"],
            priority_score=7.0,
            created_at=datetime.now(),
        )

    def test_initialization(self, review_system):
        """Test review system initialization."""
        assert review_system is not None

    @pytest.mark.asyncio
    async def test_submit_proposal(self, review_system, sample_proposal):
        """Test submitting change proposal."""
        result = await review_system.submit_proposal(sample_proposal)
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_pending_proposals(self, review_system, sample_proposal):
        """Test getting pending proposals."""
        await review_system.submit_proposal(sample_proposal)
        pending = await review_system.get_pending_proposals()
        assert isinstance(pending, list)

    @pytest.mark.asyncio
    async def test_approve_proposal(self, review_system, sample_proposal):
        """Test approving proposal."""
        proposal_id = await review_system.submit_proposal(sample_proposal)
        result = await review_system.approve_proposal(
            proposal_id,
            reviewer="reviewer@example.com",
            feedback="Looks good!"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_reject_proposal(self, review_system, sample_proposal):
        """Test rejecting proposal."""
        proposal_id = await review_system.submit_proposal(sample_proposal)
        result = await review_system.reject_proposal(
            proposal_id,
            reviewer="reviewer@example.com",
            feedback="Missing citation",
            suggested_changes=["Add proper citation"]
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_request_changes(self, review_system, sample_proposal):
        """Test requesting changes."""
        proposal_id = await review_system.submit_proposal(sample_proposal)
        result = await review_system.request_changes(
            proposal_id,
            reviewer="reviewer@example.com",
            changes_requested=["Fix formatting", "Add examples"]
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_get_proposal_status(self, review_system, sample_proposal):
        """Test getting proposal status."""
        proposal_id = await review_system.submit_proposal(sample_proposal)
        status = await review_system.get_proposal_status(proposal_id)
        assert status in ["pending", "approved", "rejected", "changes_requested"]

    @pytest.mark.asyncio
    async def test_get_review_history(self, review_system, sample_proposal):
        """Test getting review history."""
        await review_system.submit_proposal(sample_proposal)
        history = await review_system.get_review_history(sample_proposal.repo_id)
        assert isinstance(history, list)

    @pytest.mark.asyncio
    async def test_get_statistics(self, review_system):
        """Test getting review statistics."""
        stats = await review_system.get_statistics()
        assert isinstance(stats, dict)

    @pytest.mark.asyncio
    async def test_assign_reviewer(self, review_system, sample_proposal):
        """Test assigning reviewer."""
        proposal_id = await review_system.submit_proposal(sample_proposal)
        result = await review_system.assign_reviewer(
            proposal_id,
            "reviewer@example.com"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_get_reviewer_workload(self, review_system):
        """Test getting reviewer workload."""
        workload = await review_system.get_reviewer_workload("reviewer@example.com")
        assert isinstance(workload, dict)


@pytest.mark.unit
class TestHumanReviewEdgeCases:
    """Test edge cases for human review."""

    @pytest.fixture
    def review_system(self):
        """Create review system instance."""
        return HumanReviewSystem()

    @pytest.mark.asyncio
    async def test_duplicate_submission(self, review_system):
        """Test handling duplicate submissions."""
        proposal = ChangeProposal(
            repo_id="user/dataset",
            original_content="Original",
            proposed_content="New",
            changes_made=[],
            priority_score=5.0,
            created_at=datetime.now(),
        )
        await review_system.submit_proposal(proposal)
        # Second submission should be handled
        result = await review_system.submit_proposal(proposal)
        assert result is not None

    @pytest.mark.asyncio
    async def test_approve_nonexistent(self, review_system):
        """Test approving non-existent proposal."""
        result = await review_system.approve_proposal(
            "nonexistent_id",
            reviewer="reviewer@example.com",
            feedback="Test"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_concurrent_submissions(self, review_system):
        """Test concurrent submissions."""
        import asyncio

        proposals = []
        for i in range(5):
            proposal = ChangeProposal(
                repo_id=f"user/dataset{i}",
                original_content="Original",
                proposed_content="New",
                changes_made=[],
                priority_score=5.0 + i,
                created_at=datetime.now(),
            )
            proposals.append(proposal)

        # Submit concurrently
        results = await asyncio.gather(
            *[review_system.submit_proposal(p) for p in proposals]
        )
        assert all(r is not None for r in results)

    @pytest.mark.asyncio
    async def test_priority_ordering(self, review_system):
        """Test priority ordering of proposals."""
        # Submit proposals with different priorities
        for i, priority in enumerate([3.0, 8.0, 5.0, 9.0, 1.0]):
            proposal = ChangeProposal(
                repo_id=f"user/dataset{i}",
                original_content="Original",
                proposed_content="New",
                changes_made=[],
                priority_score=priority,
                created_at=datetime.now(),
            )
            await review_system.submit_proposal(proposal)

        pending = await review_system.get_pending_proposals()
        if len(pending) > 1:
            # Highest priority should be first
            assert pending[0].priority_score >= pending[-1].priority_score
