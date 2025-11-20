"""Unit tests for analysis module."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from science_card_improvement.analysis.baseline import (
    BaselineAnalyzer,
    CardSection,
    CardAnalysis,
)
from science_card_improvement.discovery.repository import RepositoryMetadata


@pytest.mark.unit
class TestCardSection:
    """Test CardSection dataclass."""

    def test_creation(self):
        """Test card section creation."""
        section = CardSection(
            name="description",
            content="This is a test dataset.",
            quality_score=0.8,
            word_count=5,
        )
        assert section.name == "description"
        assert section.quality_score == 0.8
        assert section.word_count == 5


@pytest.mark.unit
class TestCardAnalysis:
    """Test CardAnalysis dataclass."""

    def test_creation(self):
        """Test card analysis creation."""
        analysis = CardAnalysis(
            repo_id="user/dataset",
            total_score=75.0,
            completeness_score=0.8,
            structure_score=0.7,
            readability_score=0.9,
            sections=[],
            missing_sections=["citation"],
            suggestions=["Add citation"],
        )
        assert analysis.repo_id == "user/dataset"
        assert analysis.total_score == 75.0
        assert len(analysis.missing_sections) == 1


@pytest.mark.unit
class TestBaselineAnalyzer:
    """Test BaselineAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return BaselineAnalyzer()

    @pytest.fixture
    def sample_readme(self):
        """Sample README content."""
        return """
# Test Dataset

## Description
This is a comprehensive test dataset for scientific research.

## Dataset Structure
- train.csv: Training data
- test.csv: Test data

## Usage
```python
from datasets import load_dataset
dataset = load_dataset("user/dataset")
```

## License
MIT License

## Citation
@dataset{test_2024, title={Test Dataset}}
"""

    @pytest.fixture
    def minimal_readme(self):
        """Minimal README content."""
        return "# Test\n\nShort description."

    def test_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer is not None

    def test_analyze_card(self, analyzer, sample_readme):
        """Test README analysis."""
        analysis = analyzer.analyze_card(sample_readme, "user/dataset")
        assert analysis is not None
        assert analysis.repo_id == "user/dataset"
        assert analysis.total_score > 0

    def test_analyze_minimal_readme(self, analyzer, minimal_readme):
        """Test minimal README analysis."""
        analysis = analyzer.analyze_card(minimal_readme, "user/dataset")
        assert analysis.total_score < 50  # Poor README

    def test_analyze_empty_readme(self, analyzer):
        """Test empty README analysis."""
        analysis = analyzer.analyze_card("", "user/dataset")
        assert analysis.total_score == 0

    def test_identify_missing_sections(self, analyzer, minimal_readme):
        """Test identifying missing sections."""
        analysis = analyzer.analyze_card(minimal_readme, "user/dataset")
        assert len(analysis.missing_sections) > 0

    def test_generate_suggestions(self, analyzer, minimal_readme):
        """Test suggestion generation."""
        analysis = analyzer.analyze_card(minimal_readme, "user/dataset")
        assert len(analysis.suggestions) > 0

    @pytest.mark.asyncio
    async def test_compare_with_baseline(self, analyzer):
        """Test comparison with baseline."""
        target_readme = "# Target\n\nShort."
        baseline_readme = """# Baseline

## Description
Comprehensive baseline dataset.

## Usage
```python
load_dataset("user/baseline")
```

## Citation
@article{baseline}

## License
MIT
"""
        comparison = await analyzer.compare_with_baseline(
            target_readme,
            baseline_readme,
            "user/target"
        )
        assert comparison is not None

    def test_calculate_readability(self, analyzer, sample_readme):
        """Test readability calculation."""
        analysis = analyzer.analyze_card(sample_readme, "user/dataset")
        assert 0 <= analysis.readability_score <= 1

    def test_calculate_completeness(self, analyzer, sample_readme):
        """Test completeness calculation."""
        analysis = analyzer.analyze_card(sample_readme, "user/dataset")
        assert 0 <= analysis.completeness_score <= 1


@pytest.mark.unit
class TestBaselineAnalyzerEdgeCases:
    """Test edge cases for BaselineAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return BaselineAnalyzer()

    def test_readme_with_only_headers(self, analyzer):
        """Test README with only headers."""
        readme = "# Section 1\n## Section 2\n### Section 3"
        analysis = analyzer.analyze_card(readme, "user/dataset")
        assert analysis.total_score < 30

    def test_readme_with_special_characters(self, analyzer):
        """Test README with special characters."""
        readme = """# Test Dataset

## Description
Contains special chars: <>&"'`
"""
        analysis = analyzer.analyze_card(readme, "user/dataset")
        assert analysis is not None

    def test_very_long_readme(self, analyzer):
        """Test very long README."""
        long_content = "# Test\n\n" + "Content " * 5000
        analysis = analyzer.analyze_card(long_content, "user/dataset")
        assert analysis.completeness_score > 0.5

    def test_readme_with_tables(self, analyzer):
        """Test README with markdown tables."""
        readme = """# Dataset

## Statistics
| Split | Size |
|-------|------|
| Train | 1000 |
| Test  | 200  |

## License
MIT
"""
        analysis = analyzer.analyze_card(readme, "user/dataset")
        assert analysis.structure_score > 0.3

    def test_get_improvement_priority(self, analyzer, minimal_readme):
        """Test getting improvement priority."""
        analysis = analyzer.analyze_card(minimal_readme, "user/dataset")
        priority = analyzer.get_improvement_priority(analysis, downloads=1000, likes=50)
        assert priority > 0
