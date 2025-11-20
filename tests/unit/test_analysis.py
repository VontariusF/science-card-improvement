"""Unit tests for analysis module."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from science_card_improvement.analysis.baseline import (
    BaselineAnalyzer,
    CardSection,
    CardAnalysis,
)


@pytest.mark.unit
class TestCardSection:
    """Test CardSection dataclass."""

    def test_creation(self):
        """Test card section creation."""
        section = CardSection(
            name="description",
            content="This is a test dataset.",
            word_count=5,
            has_code_examples=False,
            has_citations=False,
            has_images=False,
            has_tables=False,
            has_links=True,
        )
        assert section.name == "description"
        assert section.word_count == 5
        assert section.has_links is True

    def test_default_values(self):
        """Test default values."""
        section = CardSection(
            name="test",
            content="Content",
            word_count=1,
            has_code_examples=False,
            has_citations=False,
            has_images=False,
            has_tables=False,
            has_links=False,
        )
        assert section.subsections == []
        assert section.quality_score == 0.0


@pytest.mark.unit
class TestCardAnalysis:
    """Test CardAnalysis dataclass."""

    def test_creation(self):
        """Test card analysis creation."""
        analysis = CardAnalysis(
            repo_id="user/dataset",
            repo_type="dataset",
            total_length=1000,
            sections=[],
            quality_score=75.0,
            strengths=["Good documentation"],
            weaknesses=["Missing citation"],
            missing_elements=["citation"],
            improvement_suggestions=["Add citation"],
        )
        assert analysis.repo_id == "user/dataset"
        assert analysis.quality_score == 75.0
        assert len(analysis.missing_elements) == 1

    def test_to_dict(self):
        """Test to_dict serialization."""
        section = CardSection(
            name="description",
            content="Test",
            word_count=1,
            has_code_examples=True,
            has_citations=False,
            has_images=False,
            has_tables=False,
            has_links=False,
        )
        analysis = CardAnalysis(
            repo_id="user/dataset",
            repo_type="dataset",
            total_length=100,
            sections=[section],
            quality_score=50.0,
            strengths=[],
            weaknesses=[],
            missing_elements=[],
            improvement_suggestions=[],
        )
        data = analysis.to_dict()
        assert data["repo_id"] == "user/dataset"
        assert data["quality_score"] == 50.0
        assert len(data["sections"]) == 1


@pytest.mark.unit
class TestBaselineAnalyzer:
    """Test BaselineAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance with mocked dependencies."""
        with patch('science_card_improvement.analysis.baseline.HfApi'):
            with patch('science_card_improvement.analysis.baseline.CacheManager'):
                analyzer = BaselineAnalyzer()
                analyzer.gold_standards = {}
                analyzer.poor_examples = {}
                return analyzer

    def test_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer is not None
        assert hasattr(analyzer, 'api')

    def test_gold_standard_repos_defined(self, analyzer):
        """Test gold standard repos are defined."""
        assert len(analyzer.GOLD_STANDARD_REPOS) > 0

    def test_poor_example_repos_defined(self, analyzer):
        """Test poor example repos are defined."""
        assert len(analyzer.POOR_EXAMPLE_REPOS) > 0

    def test_analyze_card_mock(self, analyzer):
        """Test analyzing a card with mocked data."""
        mock_readme = """# Test Dataset

## Description
This is a test dataset with good documentation.

## Usage
```python
from datasets import load_dataset
dataset = load_dataset("test/dataset")
```

## Citation
@article{test}

## License
MIT
"""
        with patch.object(analyzer.api, 'hf_hub_download') as mock_download:
            # Create a temp file with content
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(mock_readme)
                mock_download.return_value = f.name

            analysis = analyzer.analyze_card("test/dataset")
            assert analysis.repo_id == "test/dataset"
            assert analysis.quality_score > 0

    def test_compare_with_gold_standard(self, analyzer):
        """Test comparing with gold standard."""
        # Add a mock gold standard
        gold_analysis = CardAnalysis(
            repo_id="gold/dataset",
            repo_type="dataset",
            total_length=5000,
            sections=[],
            quality_score=95.0,
            strengths=["Comprehensive"],
            weaknesses=[],
            missing_elements=[],
            improvement_suggestions=[],
        )
        analyzer.gold_standards["gold/dataset"] = gold_analysis

        # Create target analysis
        target = CardAnalysis(
            repo_id="test/dataset",
            repo_type="dataset",
            total_length=500,
            sections=[],
            quality_score=45.0,
            strengths=[],
            weaknesses=["Too short"],
            missing_elements=["citation"],
            improvement_suggestions=["Add more content"],
        )

        # Compare
        suggestions = analyzer.generate_improvement_suggestions(target)
        assert len(suggestions) > 0


@pytest.mark.unit
class TestBaselineAnalyzerSectionParsing:
    """Test section parsing functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        with patch('science_card_improvement.analysis.baseline.HfApi'):
            with patch('science_card_improvement.analysis.baseline.CacheManager'):
                analyzer = BaselineAnalyzer()
                analyzer.gold_standards = {}
                analyzer.poor_examples = {}
                return analyzer

    def test_parse_sections_from_readme(self, analyzer):
        """Test parsing sections from README."""
        readme = """# Dataset

## Description
Test description.

## Usage
Test usage.

## License
MIT
"""
        sections = analyzer._parse_sections(readme)
        assert len(sections) >= 3

    def test_calculate_section_quality(self, analyzer):
        """Test section quality calculation."""
        section = CardSection(
            name="description",
            content="This is a comprehensive description with multiple sentences. " * 10,
            word_count=100,
            has_code_examples=True,
            has_citations=True,
            has_images=False,
            has_tables=False,
            has_links=True,
        )
        score = analyzer._calculate_section_quality(section)
        assert 0 <= score <= 1
