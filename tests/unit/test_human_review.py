"""Comprehensive unit tests for human review module."""

import json
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

from science_card_improvement.review.human import (
    ChangeProposal,
    HumanReviewSystem,
)


@pytest.mark.unit
class TestChangeProposalDataclass:
    """Test ChangeProposal dataclass."""

    def test_creation_minimal(self):
        """Test creating proposal with minimal fields."""
        proposal = ChangeProposal(
            repo_id="user/dataset",
            repo_type="dataset",
            change_type="create",
            file_path="README.md",
            original_content=None,
            proposed_content="# New Content",
            summary="Initial content",
            improvements=["Added description"],
            risks=[],
            confidence_score=0.8,
            created_at=datetime.now(),
        )
        assert proposal.repo_id == "user/dataset"
        assert proposal.change_type == "create"
        assert proposal.reviewed is False
        assert proposal.approved is False

    def test_creation_update_type(self):
        """Test creating update proposal."""
        proposal = ChangeProposal(
            repo_id="user/dataset",
            repo_type="dataset",
            change_type="update",
            file_path="README.md",
            original_content="# Old Content",
            proposed_content="# New Content",
            summary="Updated content",
            improvements=["Improved description"],
            risks=["May change formatting"],
            confidence_score=0.9,
            created_at=datetime.now(),
        )
        assert proposal.change_type == "update"
        assert proposal.original_content == "# Old Content"

    def test_default_values(self):
        """Test default values."""
        proposal = ChangeProposal(
            repo_id="user/dataset",
            repo_type="model",
            change_type="create",
            file_path="README.md",
            original_content=None,
            proposed_content="Content",
            summary="Summary",
            improvements=[],
            risks=[],
            confidence_score=0.5,
            created_at=datetime.now(),
        )
        assert proposal.reviewed is False
        assert proposal.approved is False
        assert proposal.reviewer_notes == ""


@pytest.mark.unit
class TestHumanReviewSystem:
    """Test HumanReviewSystem class."""

    @pytest.fixture
    def review_system(self, tmp_path):
        """Create review system with temp directory."""
        with patch('science_card_improvement.review.human.get_settings') as mock_settings:
            mock_settings.return_value.output_dir = tmp_path
            system = HumanReviewSystem(auto_save=False)
            return system

    def test_initialization(self, tmp_path):
        """Test system initialization."""
        with patch('science_card_improvement.review.human.get_settings') as mock_settings:
            mock_settings.return_value.output_dir = tmp_path
            system = HumanReviewSystem(auto_save=True)

            assert system.auto_save is True
            assert system.session_id is not None
            assert len(system.pending_proposals) == 0
            assert len(system.reviewed_proposals) == 0

    def test_proposals_dir_created(self, tmp_path):
        """Test proposals directory is created."""
        with patch('science_card_improvement.review.human.get_settings') as mock_settings:
            mock_settings.return_value.output_dir = tmp_path
            system = HumanReviewSystem()

            assert system.proposals_dir.exists()

    def test_create_proposal_basic(self, review_system):
        """Test creating a basic proposal."""
        proposal = review_system.create_proposal(
            repo_id="test/dataset",
            repo_type="dataset",
            file_path="README.md",
            proposed_content="# Test Content",
            summary="Test summary",
        )

        assert proposal.repo_id == "test/dataset"
        assert proposal.change_type == "create"
        assert len(review_system.pending_proposals) == 1

    def test_create_proposal_update(self, review_system):
        """Test creating an update proposal."""
        proposal = review_system.create_proposal(
            repo_id="test/dataset",
            repo_type="dataset",
            file_path="README.md",
            proposed_content="# New Content",
            original_content="# Old Content",
            summary="Update summary",
            improvements=["Added section"],
            risks=["Formatting change"],
            confidence_score=0.85,
        )

        assert proposal.change_type == "update"
        assert proposal.original_content == "# Old Content"
        assert proposal.confidence_score == 0.85

    def test_create_proposal_with_auto_save(self, tmp_path):
        """Test proposal is saved when auto_save is enabled."""
        with patch('science_card_improvement.review.human.get_settings') as mock_settings:
            mock_settings.return_value.output_dir = tmp_path
            system = HumanReviewSystem(auto_save=True)

            proposal = system.create_proposal(
                repo_id="test/dataset",
                repo_type="dataset",
                file_path="README.md",
                proposed_content="# Content",
            )

            # Check that files were created
            json_files = list(system.proposals_dir.glob("*.json"))
            md_files = list(system.proposals_dir.glob("*.md"))
            assert len(json_files) == 1
            assert len(md_files) == 1

    def test_programmatic_review_returns_false(self, review_system):
        """Test programmatic review always returns False (no auto-approve)."""
        proposal = review_system.create_proposal(
            repo_id="test/dataset",
            repo_type="dataset",
            file_path="README.md",
            proposed_content="# Content",
        )

        result = review_system.review_proposal(proposal, interactive=False)

        assert result is False

    def test_save_proposal(self, review_system):
        """Test saving proposal to disk."""
        proposal = ChangeProposal(
            repo_id="test/dataset",
            repo_type="dataset",
            change_type="create",
            file_path="README.md",
            original_content=None,
            proposed_content="# Test Content\n\nDescription here.",
            summary="Test summary",
            improvements=["Added description"],
            risks=[],
            confidence_score=0.8,
            created_at=datetime.now(),
        )

        filepath = review_system._save_proposal(proposal)

        assert filepath.exists()
        assert filepath.suffix == ".json"

        # Check content file
        content_file = filepath.with_suffix(".md")
        assert content_file.exists()
        assert content_file.read_text() == proposal.proposed_content

    def test_export_proposal(self, review_system):
        """Test exporting proposal for external review."""
        proposal = ChangeProposal(
            repo_id="test/dataset",
            repo_type="dataset",
            change_type="update",
            file_path="README.md",
            original_content="# Old",
            proposed_content="# New\n\nBetter content.",
            summary="Improved content",
            improvements=["Better description", "Added examples"],
            risks=["Formatting"],
            confidence_score=0.9,
            created_at=datetime.now(),
        )

        filepath = review_system._export_proposal(proposal)

        assert filepath.exists()
        content = filepath.read_text()
        assert "test/dataset" in content
        assert "Better description" in content
        assert "# New" in content

    def test_generate_pr_description(self, review_system):
        """Test generating PR description."""
        proposal = ChangeProposal(
            repo_id="test/dataset",
            repo_type="dataset",
            change_type="update",
            file_path="README.md",
            original_content="# Old",
            proposed_content="# New",
            summary="Improved documentation",
            improvements=["Added description", "Added citation"],
            risks=[],
            confidence_score=0.85,
            created_at=datetime.now(),
            reviewed=True,
            approved=True,
            reviewer_notes="Looks good",
        )

        description = review_system._generate_pr_description(proposal)

        assert "Summary" in description
        assert "Improved documentation" in description
        assert "Added description" in description
        assert "Looks good" in description
        assert "Science Card Improvement" in description

    def test_create_pr_draft_success(self, review_system):
        """Test creating PR draft from approved proposal."""
        proposal = ChangeProposal(
            repo_id="test/dataset",
            repo_type="dataset",
            change_type="update",
            file_path="README.md",
            original_content="# Old",
            proposed_content="# New",
            summary="Updated",
            improvements=["Better docs"],
            risks=[],
            confidence_score=0.9,
            created_at=datetime.now(),
            reviewed=True,
            approved=True,
        )

        draft = review_system.create_pr_draft(proposal)

        assert draft["repo_id"] == "test/dataset"
        assert draft["auto_submit"] is False
        assert draft["requires_confirmation"] is True
        assert "improve-card" in draft["branch"]

    def test_create_pr_draft_unapproved_raises(self, review_system):
        """Test creating PR draft from unapproved proposal raises error."""
        proposal = ChangeProposal(
            repo_id="test/dataset",
            repo_type="dataset",
            change_type="create",
            file_path="README.md",
            original_content=None,
            proposed_content="# Content",
            summary="Summary",
            improvements=[],
            risks=[],
            confidence_score=0.5,
            created_at=datetime.now(),
            approved=False,
        )

        with pytest.raises(ValueError, match="unapproved"):
            review_system.create_pr_draft(proposal)

    def test_get_statistics_empty(self, review_system):
        """Test statistics with no proposals."""
        stats = review_system.get_statistics()

        assert stats["pending_proposals"] == 0
        assert stats["reviewed_proposals"] == 0
        assert stats["approved"] == 0
        assert stats["rejected"] == 0
        assert stats["approval_rate"] == 0

    def test_get_statistics_with_proposals(self, review_system):
        """Test statistics with proposals."""
        # Create some proposals
        for i in range(3):
            proposal = review_system.create_proposal(
                repo_id=f"test/dataset{i}",
                repo_type="dataset",
                file_path="README.md",
                proposed_content=f"# Content {i}",
            )

        # Mark some as reviewed
        review_system.pending_proposals[0].reviewed = True
        review_system.pending_proposals[0].approved = True
        review_system.reviewed_proposals.append(review_system.pending_proposals[0])

        review_system.pending_proposals[1].reviewed = True
        review_system.pending_proposals[1].approved = False
        review_system.reviewed_proposals.append(review_system.pending_proposals[1])

        stats = review_system.get_statistics()

        assert stats["pending_proposals"] == 3
        assert stats["reviewed_proposals"] == 2
        assert stats["approved"] == 1
        assert stats["rejected"] == 1
        assert stats["approval_rate"] == 0.5


@pytest.mark.unit
class TestHumanReviewSystemEdgeCases:
    """Test edge cases for human review system."""

    @pytest.fixture
    def review_system(self, tmp_path):
        """Create review system with temp directory."""
        with patch('science_card_improvement.review.human.get_settings') as mock_settings:
            mock_settings.return_value.output_dir = tmp_path
            system = HumanReviewSystem(auto_save=False)
            return system

    def test_proposal_with_empty_improvements(self, review_system):
        """Test proposal with empty improvements list."""
        proposal = review_system.create_proposal(
            repo_id="test/dataset",
            repo_type="dataset",
            file_path="README.md",
            proposed_content="# Content",
            improvements=[],
        )

        assert proposal.improvements == []

    def test_proposal_with_long_content(self, review_system):
        """Test proposal with very long content."""
        long_content = "# Title\n\n" + "Test paragraph. " * 1000
        proposal = review_system.create_proposal(
            repo_id="test/dataset",
            repo_type="dataset",
            file_path="README.md",
            proposed_content=long_content,
        )

        assert len(proposal.proposed_content) > 10000

    def test_proposal_with_special_repo_id(self, review_system):
        """Test proposal with special characters in repo ID."""
        proposal = review_system.create_proposal(
            repo_id="user-name/dataset_v2.0",
            repo_type="dataset",
            file_path="README.md",
            proposed_content="# Content",
        )

        assert proposal.repo_id == "user-name/dataset_v2.0"

    def test_multiple_proposals_same_repo(self, review_system):
        """Test creating multiple proposals for same repo."""
        for i in range(3):
            review_system.create_proposal(
                repo_id="test/dataset",
                repo_type="dataset",
                file_path="README.md",
                proposed_content=f"# Content v{i}",
            )

        assert len(review_system.pending_proposals) == 3

    def test_pr_draft_saves_to_disk(self, review_system):
        """Test PR draft is saved to proposals directory."""
        proposal = ChangeProposal(
            repo_id="test/dataset",
            repo_type="dataset",
            change_type="create",
            file_path="README.md",
            original_content=None,
            proposed_content="# Content",
            summary="Summary",
            improvements=["Added content"],
            risks=[],
            confidence_score=0.9,
            created_at=datetime.now(),
            reviewed=True,
            approved=True,
        )

        review_system.create_pr_draft(proposal)

        # Check draft file exists
        draft_files = list(review_system.proposals_dir.glob("pr_draft_*.json"))
        assert len(draft_files) == 1

        # Verify content
        with open(draft_files[0]) as f:
            data = json.load(f)
            assert data["repo_id"] == "test/dataset"
            assert data["auto_submit"] is False

    def test_model_repo_type(self, review_system):
        """Test proposal for model type."""
        proposal = review_system.create_proposal(
            repo_id="user/model",
            repo_type="model",
            file_path="README.md",
            proposed_content="# Model Card",
        )

        assert proposal.repo_type == "model"

    def test_confidence_score_boundaries(self, review_system):
        """Test confidence score at boundaries."""
        low_confidence = review_system.create_proposal(
            repo_id="test/dataset1",
            repo_type="dataset",
            file_path="README.md",
            proposed_content="# Content",
            confidence_score=0.0,
        )
        assert low_confidence.confidence_score == 0.0

        high_confidence = review_system.create_proposal(
            repo_id="test/dataset2",
            repo_type="dataset",
            file_path="README.md",
            proposed_content="# Content",
            confidence_score=1.0,
        )
        assert high_confidence.confidence_score == 1.0
