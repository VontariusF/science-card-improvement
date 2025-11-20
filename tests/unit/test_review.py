"""Unit tests for human review module."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from science_card_improvement.review.human import (
    ChangeProposal,
    HumanReviewSystem,
)


@pytest.mark.unit
class TestChangeProposal:
    """Test ChangeProposal dataclass."""

    def test_creation(self):
        """Test change proposal creation."""
        proposal = ChangeProposal(
            repo_id="user/dataset",
            repo_type="dataset",
            change_type="update",
            file_path="README.md",
            original_content="# Old\n\nOld content",
            proposed_content="# New\n\nNew content",
            summary="Updated documentation",
            improvements=["Added license", "Added citation"],
            risks=["May need review"],
            confidence_score=0.85,
            created_at=datetime.now(),
        )
        assert proposal.repo_id == "user/dataset"
        assert len(proposal.improvements) == 2
        assert proposal.confidence_score == 0.85

    def test_default_values(self):
        """Test default values."""
        proposal = ChangeProposal(
            repo_id="user/dataset",
            repo_type="dataset",
            change_type="create",
            file_path="README.md",
            original_content=None,
            proposed_content="New content",
            summary="Created README",
            improvements=[],
            risks=[],
            confidence_score=0.9,
            created_at=datetime.now(),
        )
        assert proposal.reviewed is False
        assert proposal.approved is False
        assert proposal.reviewer_notes == ""


@pytest.mark.unit
class TestHumanReviewSystem:
    """Test HumanReviewSystem class."""

    @pytest.fixture
    def review_system(self):
        """Create review system instance."""
        with patch('science_card_improvement.review.human.get_settings') as mock_settings:
            mock_settings.return_value.output_dir = MagicMock()
            mock_settings.return_value.output_dir.__truediv__ = MagicMock(return_value=MagicMock())
            return HumanReviewSystem(auto_save=False)

    @pytest.fixture
    def sample_proposal(self):
        """Create sample change proposal."""
        return ChangeProposal(
            repo_id="user/dataset",
            repo_type="dataset",
            change_type="update",
            file_path="README.md",
            original_content="# Old Content",
            proposed_content="# New Content\n\n## Description\nImproved",
            summary="Added description section",
            improvements=["Added description"],
            risks=[],
            confidence_score=0.8,
            created_at=datetime.now(),
        )

    def test_initialization(self, review_system):
        """Test review system initialization."""
        assert review_system is not None
        assert review_system.pending_proposals == []
        assert review_system.reviewed_proposals == []

    def test_add_proposal(self, review_system, sample_proposal):
        """Test adding proposal to queue."""
        review_system.pending_proposals.append(sample_proposal)
        assert len(review_system.pending_proposals) == 1

    def test_proposal_attributes(self, sample_proposal):
        """Test proposal has all required attributes."""
        assert hasattr(sample_proposal, 'repo_id')
        assert hasattr(sample_proposal, 'repo_type')
        assert hasattr(sample_proposal, 'change_type')
        assert hasattr(sample_proposal, 'file_path')
        assert hasattr(sample_proposal, 'original_content')
        assert hasattr(sample_proposal, 'proposed_content')
        assert hasattr(sample_proposal, 'summary')
        assert hasattr(sample_proposal, 'improvements')
        assert hasattr(sample_proposal, 'risks')
        assert hasattr(sample_proposal, 'confidence_score')

    def test_multiple_proposals(self, review_system):
        """Test handling multiple proposals."""
        for i in range(3):
            proposal = ChangeProposal(
                repo_id=f"user/dataset{i}",
                repo_type="dataset",
                change_type="update",
                file_path="README.md",
                original_content="Original",
                proposed_content="New",
                summary=f"Update {i}",
                improvements=[],
                risks=[],
                confidence_score=0.7 + i * 0.1,
                created_at=datetime.now(),
            )
            review_system.pending_proposals.append(proposal)

        assert len(review_system.pending_proposals) == 3

    def test_approve_proposal(self, review_system, sample_proposal):
        """Test approving a proposal."""
        review_system.pending_proposals.append(sample_proposal)
        proposal = review_system.pending_proposals[0]
        proposal.reviewed = True
        proposal.approved = True
        proposal.reviewer_notes = "Looks good!"

        assert proposal.approved is True
        assert proposal.reviewer_notes == "Looks good!"

    def test_reject_proposal(self, review_system, sample_proposal):
        """Test rejecting a proposal."""
        review_system.pending_proposals.append(sample_proposal)
        proposal = review_system.pending_proposals[0]
        proposal.reviewed = True
        proposal.approved = False
        proposal.reviewer_notes = "Missing citation"

        assert proposal.approved is False

    def test_session_id_format(self, review_system):
        """Test session ID format."""
        assert review_system.session_id is not None
        # Format: YYYYMMDD_HHMMSS
        assert len(review_system.session_id) == 15
        assert "_" in review_system.session_id


@pytest.mark.unit
class TestHumanReviewEdgeCases:
    """Test edge cases for human review."""

    @pytest.fixture
    def review_system(self):
        """Create review system instance."""
        with patch('science_card_improvement.review.human.get_settings') as mock_settings:
            mock_settings.return_value.output_dir = MagicMock()
            mock_settings.return_value.output_dir.__truediv__ = MagicMock(return_value=MagicMock())
            return HumanReviewSystem(auto_save=False)

    def test_empty_improvements(self):
        """Test proposal with no improvements."""
        proposal = ChangeProposal(
            repo_id="user/dataset",
            repo_type="dataset",
            change_type="update",
            file_path="README.md",
            original_content="Original",
            proposed_content="New",
            summary="Minor update",
            improvements=[],
            risks=[],
            confidence_score=0.5,
            created_at=datetime.now(),
        )
        assert proposal.improvements == []

    def test_high_risk_proposal(self):
        """Test proposal with high risks."""
        proposal = ChangeProposal(
            repo_id="user/dataset",
            repo_type="dataset",
            change_type="update",
            file_path="README.md",
            original_content="Original",
            proposed_content="New",
            summary="Risky update",
            improvements=["Better format"],
            risks=["May break links", "License change", "Major rewrite"],
            confidence_score=0.3,
            created_at=datetime.now(),
        )
        assert len(proposal.risks) == 3
        assert proposal.confidence_score < 0.5

    def test_create_change_type(self):
        """Test create change type."""
        proposal = ChangeProposal(
            repo_id="user/dataset",
            repo_type="dataset",
            change_type="create",
            file_path="README.md",
            original_content=None,
            proposed_content="# New README",
            summary="Created README",
            improvements=["Added README"],
            risks=[],
            confidence_score=0.9,
            created_at=datetime.now(),
        )
        assert proposal.change_type == "create"
        assert proposal.original_content is None

    def test_model_repo_type(self):
        """Test model repository type."""
        proposal = ChangeProposal(
            repo_id="user/model",
            repo_type="model",
            change_type="update",
            file_path="README.md",
            original_content="Old",
            proposed_content="New",
            summary="Updated model card",
            improvements=[],
            risks=[],
            confidence_score=0.8,
            created_at=datetime.now(),
        )
        assert proposal.repo_type == "model"
