"""Unit tests for input validators."""

import pytest
from pydantic import ValidationError as PydanticValidationError

from science_card_improvement.validators.input import (
    RepositoryIdValidator,
    DiscoveryRequestValidator,
    CardGenerationRequestValidator,
    PRSubmissionValidator,
    TagSuggestionValidator,
    BatchProcessingValidator,
)


@pytest.mark.unit
class TestRepositoryIdValidator:
    """Test RepositoryIdValidator class."""

    def test_valid_repo_id(self):
        """Test valid repository ID."""
        validator = RepositoryIdValidator(repo_id="user/dataset", repo_type="dataset")
        assert validator.repo_id == "user/dataset"
        assert validator.repo_type == "dataset"

    def test_valid_repo_id_with_special_chars(self):
        """Test valid repository ID with hyphens and underscores."""
        validator = RepositoryIdValidator(repo_id="my-org/my_dataset-v1", repo_type="model")
        assert validator.repo_id == "my-org/my_dataset-v1"

    def test_valid_repo_id_with_dots(self):
        """Test valid repository ID with dots."""
        validator = RepositoryIdValidator(repo_id="org.name/dataset.v1", repo_type="dataset")
        assert validator.repo_id == "org.name/dataset.v1"

    def test_invalid_repo_id_no_slash(self):
        """Test invalid repository ID without slash."""
        with pytest.raises(PydanticValidationError):
            RepositoryIdValidator(repo_id="invalid", repo_type="dataset")

    def test_invalid_repo_id_empty(self):
        """Test invalid empty repository ID."""
        with pytest.raises(PydanticValidationError):
            RepositoryIdValidator(repo_id="", repo_type="dataset")

    def test_invalid_repo_id_special_chars(self):
        """Test invalid repository ID with special characters."""
        with pytest.raises(PydanticValidationError):
            RepositoryIdValidator(repo_id="user/data@set!", repo_type="dataset")

    def test_invalid_repo_type(self):
        """Test invalid repository type."""
        with pytest.raises(PydanticValidationError):
            RepositoryIdValidator(repo_id="user/dataset", repo_type="invalid")

    def test_valid_repo_types(self):
        """Test all valid repository types."""
        for repo_type in ["dataset", "model", "space"]:
            validator = RepositoryIdValidator(repo_id="user/repo", repo_type=repo_type)
            assert validator.repo_type == repo_type


@pytest.mark.unit
class TestDiscoveryRequestValidator:
    """Test DiscoveryRequestValidator class."""

    def test_default_values(self):
        """Test default values."""
        validator = DiscoveryRequestValidator()
        assert validator.repo_type == "both"
        assert validator.limit == 100
        assert validator.keywords is None
        assert validator.sort_by == "priority"
        assert validator.filters is None

    def test_custom_values(self):
        """Test custom values."""
        validator = DiscoveryRequestValidator(
            repo_type="dataset",
            limit=50,
            keywords=["biology", "genomics"],
            sort_by="downloads",
        )
        assert validator.repo_type == "dataset"
        assert validator.limit == 50
        assert validator.keywords == ["biology", "genomics"]
        assert validator.sort_by == "downloads"

    def test_invalid_repo_type(self):
        """Test invalid repository type."""
        with pytest.raises(PydanticValidationError):
            DiscoveryRequestValidator(repo_type="invalid")

    def test_limit_boundaries(self):
        """Test limit boundaries."""
        # Valid limits
        DiscoveryRequestValidator(limit=1)
        DiscoveryRequestValidator(limit=1000)

        # Invalid limits
        with pytest.raises(PydanticValidationError):
            DiscoveryRequestValidator(limit=0)
        with pytest.raises(PydanticValidationError):
            DiscoveryRequestValidator(limit=1001)

    def test_invalid_sort_by(self):
        """Test invalid sort criteria."""
        with pytest.raises(PydanticValidationError):
            DiscoveryRequestValidator(sort_by="invalid")

    def test_valid_sort_options(self):
        """Test all valid sort options."""
        for sort_by in ["downloads", "likes", "updated", "priority", "readme_quality"]:
            validator = DiscoveryRequestValidator(sort_by=sort_by)
            assert validator.sort_by == sort_by

    def test_keyword_validation(self):
        """Test keyword validation."""
        # Valid keywords
        validator = DiscoveryRequestValidator(keywords=["bio", "chem"])
        assert validator.keywords == ["bio", "chem"]

        # Too short keyword
        with pytest.raises(PydanticValidationError):
            DiscoveryRequestValidator(keywords=["a"])

    def test_filter_validation(self):
        """Test filter validation."""
        # Valid filters
        validator = DiscoveryRequestValidator(
            filters={"min_downloads": 100, "has_readme": True}
        )
        assert validator.filters["min_downloads"] == 100

        # Invalid filter key
        with pytest.raises(PydanticValidationError):
            DiscoveryRequestValidator(filters={"invalid_filter": 100})

        # Invalid filter type
        with pytest.raises(PydanticValidationError):
            DiscoveryRequestValidator(filters={"min_downloads": "not_an_int"})

        # Negative value
        with pytest.raises(PydanticValidationError):
            DiscoveryRequestValidator(filters={"min_downloads": -1})


@pytest.mark.unit
class TestCardGenerationRequestValidator:
    """Test CardGenerationRequestValidator class."""

    def test_valid_request(self):
        """Test valid card generation request."""
        validator = CardGenerationRequestValidator(
            repo_id="user/dataset",
            repo_type="dataset",
            template="comprehensive",
        )
        assert validator.repo_id == "user/dataset"
        assert validator.template == "comprehensive"

    def test_default_values(self):
        """Test default values."""
        validator = CardGenerationRequestValidator(repo_id="user/dataset")
        assert validator.repo_type == "dataset"
        assert validator.template == "comprehensive"
        assert validator.include_examples is True
        assert validator.include_citation is True

    def test_invalid_template(self):
        """Test invalid template."""
        with pytest.raises(PydanticValidationError):
            CardGenerationRequestValidator(
                repo_id="user/dataset",
                template="invalid"
            )

    def test_valid_templates(self):
        """Test all valid templates."""
        for template in ["comprehensive", "minimal", "scientific", "medical", "custom"]:
            validator = CardGenerationRequestValidator(
                repo_id="user/dataset",
                template=template
            )
            assert validator.template == template

    def test_custom_fields_validation(self):
        """Test custom fields validation."""
        # Valid custom fields
        validator = CardGenerationRequestValidator(
            repo_id="user/dataset",
            custom_fields={"field1": "value1"}
        )
        assert validator.custom_fields == {"field1": "value1"}

        # Too many custom fields
        too_many_fields = {f"field{i}": f"value{i}" for i in range(25)}
        with pytest.raises(PydanticValidationError):
            CardGenerationRequestValidator(
                repo_id="user/dataset",
                custom_fields=too_many_fields
            )


@pytest.mark.unit
class TestTagSuggestionValidator:
    """Test TagSuggestionValidator class."""

    def test_valid_request(self):
        """Test valid tag suggestion request."""
        validator = TagSuggestionValidator(
            repo_id="user/dataset",
            existing_tags=["biology", "genomics"],
            max_suggestions=5
        )
        assert validator.repo_id == "user/dataset"
        assert len(validator.existing_tags) == 2
        assert validator.max_suggestions == 5

    def test_default_values(self):
        """Test default values."""
        validator = TagSuggestionValidator(repo_id="user/dataset")
        assert validator.repo_type == "dataset"
        assert validator.existing_tags == []
        assert validator.max_suggestions == 10
        assert validator.include_domain_tags is True

    def test_max_suggestions_boundaries(self):
        """Test max suggestions boundaries."""
        # Valid
        TagSuggestionValidator(repo_id="user/dataset", max_suggestions=1)
        TagSuggestionValidator(repo_id="user/dataset", max_suggestions=50)

        # Invalid
        with pytest.raises(PydanticValidationError):
            TagSuggestionValidator(repo_id="user/dataset", max_suggestions=0)
        with pytest.raises(PydanticValidationError):
            TagSuggestionValidator(repo_id="user/dataset", max_suggestions=51)

    def test_tag_validation(self):
        """Test existing tags validation."""
        # Valid tags
        validator = TagSuggestionValidator(
            repo_id="user/dataset",
            existing_tags=["a", "valid-tag"]
        )
        assert len(validator.existing_tags) == 2

        # Empty tag
        with pytest.raises(PydanticValidationError):
            TagSuggestionValidator(
                repo_id="user/dataset",
                existing_tags=[""]
            )


@pytest.mark.unit
class TestBatchProcessingValidator:
    """Test BatchProcessingValidator class."""

    def test_valid_request(self):
        """Test valid batch processing request."""
        validator = BatchProcessingValidator(
            repo_ids=["user/repo1", "user/repo2"],
            operation="assess_quality"
        )
        assert len(validator.repo_ids) == 2
        assert validator.operation == "assess_quality"

    def test_default_values(self):
        """Test default values."""
        validator = BatchProcessingValidator(
            repo_ids=["user/repo"],
            operation="assess_quality"
        )
        assert validator.parallel_workers == 5
        assert validator.continue_on_error is True
        assert validator.dry_run is False

    def test_invalid_operation(self):
        """Test invalid operation."""
        with pytest.raises(PydanticValidationError):
            BatchProcessingValidator(
                repo_ids=["user/repo"],
                operation="invalid"
            )

    def test_valid_operations(self):
        """Test all valid operations."""
        for operation in ["assess_quality", "generate_cards", "submit_prs", "suggest_tags", "export_metadata"]:
            validator = BatchProcessingValidator(
                repo_ids=["user/repo"],
                operation=operation
            )
            assert validator.operation == operation

    def test_parallel_workers_boundaries(self):
        """Test parallel workers boundaries."""
        # Valid
        BatchProcessingValidator(repo_ids=["user/repo"], operation="assess_quality", parallel_workers=1)
        BatchProcessingValidator(repo_ids=["user/repo"], operation="assess_quality", parallel_workers=20)

        # Invalid
        with pytest.raises(PydanticValidationError):
            BatchProcessingValidator(repo_ids=["user/repo"], operation="assess_quality", parallel_workers=0)
        with pytest.raises(PydanticValidationError):
            BatchProcessingValidator(repo_ids=["user/repo"], operation="assess_quality", parallel_workers=21)

    def test_invalid_repo_id_in_batch(self):
        """Test invalid repository ID in batch."""
        with pytest.raises(PydanticValidationError):
            BatchProcessingValidator(
                repo_ids=["user/repo", "invalid"],
                operation="assess_quality"
            )

    def test_empty_repo_ids(self):
        """Test empty repository IDs list."""
        with pytest.raises(PydanticValidationError):
            BatchProcessingValidator(
                repo_ids=[],
                operation="assess_quality"
            )
