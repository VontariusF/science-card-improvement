"""Baseline analyzer for comparing and learning from good vs bad dataset/model cards."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from huggingface_hub import HfApi

from src.config.settings import get_settings
from src.exceptions.custom_exceptions import RepositoryNotFoundError
from src.utils.cache import CacheManager
from src.utils.logger import LoggerMixin


@dataclass
class CardSection:
    """Represents a section of a dataset/model card."""

    name: str
    content: str
    word_count: int
    has_code_examples: bool
    has_citations: bool
    has_images: bool
    has_tables: bool
    has_links: bool
    subsections: List[str] = field(default_factory=list)
    quality_score: float = 0.0


@dataclass
class CardAnalysis:
    """Complete analysis of a dataset/model card."""

    repo_id: str
    repo_type: str
    total_length: int
    sections: List[CardSection]
    quality_score: float
    strengths: List[str]
    weaknesses: List[str]
    missing_elements: List[str]
    improvement_suggestions: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "repo_id": self.repo_id,
            "repo_type": self.repo_type,
            "total_length": self.total_length,
            "sections": [
                {
                    "name": s.name,
                    "word_count": s.word_count,
                    "has_code_examples": s.has_code_examples,
                    "has_citations": s.has_citations,
                    "quality_score": s.quality_score,
                }
                for s in self.sections
            ],
            "quality_score": self.quality_score,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "missing_elements": self.missing_elements,
            "improvement_suggestions": self.improvement_suggestions,
            "metadata": self.metadata,
        }


class BaselineAnalyzer(LoggerMixin):
    """Analyzes dataset/model cards against known good and bad examples."""

    # Known exemplary cards (A+ quality)
    GOLD_STANDARD_REPOS = [
        "tahoebio/Tahoe-100M",  # Excellent dataset card example
        "bigscience/bloom",      # Great model card example
        "allenai/olmo",          # Comprehensive documentation
    ]

    # Known poor cards (needs improvement)
    POOR_EXAMPLE_REPOS = [
        "arcinstitute/opengenome2",  # Bone dry dataset card
    ]

    # Essential sections for a good card
    ESSENTIAL_SECTIONS = [
        "description",
        "dataset_structure",  # or "model_architecture" for models
        "usage",
        "data_sources",       # or "training_data" for models
        "license",
        "citation",
        "limitations",
    ]

    # High-value sections that make cards excellent
    HIGH_VALUE_SECTIONS = [
        "motivation",
        "data_collection",
        "preprocessing",
        "evaluation",
        "ethical_considerations",
        "acknowledgments",
        "changelog",
        "contact",
    ]

    def __init__(
        self,
        api_token: Optional[str] = None,
        cache_enabled: bool = True,
        auto_learn: bool = True,
    ):
        """Initialize the baseline analyzer.

        Args:
            api_token: Hugging Face API token
            cache_enabled: Enable caching of analyses
            auto_learn: Automatically learn from new examples
        """
        self.settings = get_settings()
        self.api = HfApi(token=api_token or self.settings.hf_token.get_secret_value() if self.settings.hf_token else None)
        self.cache = CacheManager() if cache_enabled else None
        self.auto_learn = auto_learn

        # Load baseline analyses
        self.gold_standards: Dict[str, CardAnalysis] = {}
        self.poor_examples: Dict[str, CardAnalysis] = {}
        self._load_baselines()

    def _load_baselines(self) -> None:
        """Load and analyze baseline examples."""
        self.log_info("Loading baseline examples for comparison")

        # Analyze gold standard examples
        for repo_id in self.GOLD_STANDARD_REPOS:
            try:
                analysis = self.analyze_card(repo_id)
                self.gold_standards[repo_id] = analysis
                self.log_info(f"Loaded gold standard: {repo_id} (score: {analysis.quality_score:.2f})")
            except Exception as e:
                self.log_error(f"Failed to load gold standard {repo_id}", exception=e)

        # Analyze poor examples
        for repo_id in self.POOR_EXAMPLE_REPOS:
            try:
                analysis = self.analyze_card(repo_id)
                self.poor_examples[repo_id] = analysis
                self.log_info(f"Loaded poor example: {repo_id} (score: {analysis.quality_score:.2f})")
            except Exception as e:
                self.log_error(f"Failed to load poor example {repo_id}", exception=e)

    def analyze_card(self, repo_id: str, repo_type: str = "dataset") -> CardAnalysis:
        """Analyze a dataset/model card comprehensively.

        Args:
            repo_id: Repository ID (e.g., "org/dataset")
            repo_type: Type of repository ("dataset" or "model")

        Returns:
            Complete card analysis
        """
        # Try to get from cache
        if self.cache:
            cache_key = f"analysis:{repo_id}:{repo_type}"
            # Note: Synchronous cache access for now
            # cached = self.cache.get(cache_key)
            # if cached:
            #     return CardAnalysis(**cached)

        try:
            # Download README
            readme_path = self.api.hf_hub_download(
                repo_id=repo_id,
                filename="README.md",
                repo_type=repo_type,
            )

            with open(readme_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.log_error(f"Failed to fetch README for {repo_id}", exception=e)
            raise RepositoryNotFoundError(repo_id, repo_type)

        # Analyze the content
        sections = self._extract_sections(content)
        quality_score = self._calculate_quality_score(sections, content)
        strengths = self._identify_strengths(sections, content)
        weaknesses = self._identify_weaknesses(sections, content)
        missing_elements = self._find_missing_elements(sections)

        # Generate improvement suggestions
        suggestions = self._generate_suggestions(
            sections,
            missing_elements,
            weaknesses,
            content
        )

        analysis = CardAnalysis(
            repo_id=repo_id,
            repo_type=repo_type,
            total_length=len(content),
            sections=sections,
            quality_score=quality_score,
            strengths=strengths,
            weaknesses=weaknesses,
            missing_elements=missing_elements,
            improvement_suggestions=suggestions,
            metadata={
                "analyzed_at": datetime.utcnow().isoformat(),
                "analyzer_version": "1.0.0",
            }
        )

        # Cache the analysis
        if self.cache:
            # Note: Synchronous cache access for now
            # self.cache.set(cache_key, analysis.to_dict(), ttl=86400)  # 24 hours
            pass

        return analysis

    def _extract_sections(self, content: str) -> List[CardSection]:
        """Extract and analyze sections from README content."""
        sections = []

        # Split by headers
        header_pattern = r"^(#{1,3})\s+(.+)$"
        lines = content.split("\n")

        current_section = None
        current_content = []

        for line in lines:
            header_match = re.match(header_pattern, line)

            if header_match:
                # Save previous section
                if current_section:
                    section_content = "\n".join(current_content)
                    sections.append(self._analyze_section(current_section, section_content))

                # Start new section
                level = len(header_match.group(1))
                current_section = header_match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)

        # Don't forget the last section
        if current_section:
            section_content = "\n".join(current_content)
            sections.append(self._analyze_section(current_section, section_content))

        return sections

    def _analyze_section(self, name: str, content: str) -> CardSection:
        """Analyze a single section of the card."""
        return CardSection(
            name=name,
            content=content,
            word_count=len(content.split()),
            has_code_examples=bool(re.search(r"```[\s\S]*?```", content)),
            has_citations=bool(re.search(r"@\w+|\\cite|arXiv|\[[\d,\s]+\]", content)),
            has_images=bool(re.search(r"!\[.*?\]\(.*?\)", content)),
            has_tables=bool(re.search(r"\|.*\|.*\|", content)),
            has_links=bool(re.search(r"\[.*?\]\(.*?\)", content)),
            subsections=re.findall(r"^#{4,6}\s+(.+)$", content, re.MULTILINE),
            quality_score=self._score_section_quality(name, content),
        )

    def _score_section_quality(self, name: str, content: str) -> float:
        """Score the quality of a section (0-1)."""
        score = 0.0

        # Length scoring
        word_count = len(content.split())
        if word_count > 200:
            score += 0.3
        elif word_count > 100:
            score += 0.2
        elif word_count > 50:
            score += 0.1

        # Content richness
        if re.search(r"```[\s\S]*?```", content):  # Code examples
            score += 0.2
        if re.search(r"!\[.*?\]\(.*?\)", content):  # Images
            score += 0.1
        if re.search(r"\|.*\|.*\|", content):  # Tables
            score += 0.1
        if re.search(r"\[.*?\]\(.*?\)", content):  # Links
            score += 0.1

        # Specific high-value patterns
        if "example" in content.lower():
            score += 0.1
        if "citation" in name.lower() and "@" in content:
            score += 0.1

        return min(1.0, score)

    def _calculate_quality_score(self, sections: List[CardSection], content: str) -> float:
        """Calculate overall quality score (0-100)."""
        score = 0.0

        # Length score (up to 20 points)
        length_score = min(20, len(content) / 100)
        score += length_score

        # Section coverage (up to 40 points)
        section_names = [s.name.lower() for s in sections]
        essential_coverage = sum(
            5 for section in self.ESSENTIAL_SECTIONS
            if any(section in name for name in section_names)
        )
        score += essential_coverage

        high_value_coverage = sum(
            3 for section in self.HIGH_VALUE_SECTIONS
            if any(section in name for name in section_names)
        )
        score += high_value_coverage

        # Content quality (up to 30 points)
        if sections:
            avg_section_quality = sum(s.quality_score for s in sections) / len(sections)
            score += avg_section_quality * 30

        # Special features (up to 10 points)
        has_code = any(s.has_code_examples for s in sections)
        has_citations = any(s.has_citations for s in sections)
        has_visuals = any(s.has_images or s.has_tables for s in sections)

        if has_code:
            score += 4
        if has_citations:
            score += 3
        if has_visuals:
            score += 3

        return min(100, score)

    def _identify_strengths(self, sections: List[CardSection], content: str) -> List[str]:
        """Identify strengths in the card."""
        strengths = []

        if len(content) > 2000:
            strengths.append("Comprehensive documentation")

        if any(s.has_code_examples for s in sections):
            strengths.append("Includes code examples")

        if any(s.has_citations for s in sections):
            strengths.append("Provides citations and references")

        if any(s.has_images or s.has_tables for s in sections):
            strengths.append("Uses visual aids (images/tables)")

        section_names = [s.name.lower() for s in sections]
        if any("limitation" in name for name in section_names):
            strengths.append("Discusses limitations transparently")

        if any("ethic" in name for name in section_names):
            strengths.append("Addresses ethical considerations")

        if len(sections) > 10:
            strengths.append("Well-structured with many sections")

        return strengths

    def _identify_weaknesses(self, sections: List[CardSection], content: str) -> List[str]:
        """Identify weaknesses in the card."""
        weaknesses = []

        if len(content) < 500:
            weaknesses.append("Documentation is too brief")

        if not any(s.has_code_examples for s in sections):
            weaknesses.append("No code examples provided")

        if not any(s.has_citations for s in sections):
            weaknesses.append("Missing citations or references")

        section_names = [s.name.lower() for s in sections]
        if not any("usage" in name or "example" in name for name in section_names):
            weaknesses.append("No usage instructions")

        if not any("license" in name for name in section_names):
            weaknesses.append("License information not clearly stated")

        # Check for very short sections
        short_sections = [s for s in sections if s.word_count < 20]
        if len(short_sections) > len(sections) / 2:
            weaknesses.append("Many sections are too brief")

        return weaknesses

    def _find_missing_elements(self, sections: List[CardSection]) -> List[str]:
        """Find missing essential elements."""
        missing = []
        section_names = [s.name.lower() for s in sections]

        for essential in self.ESSENTIAL_SECTIONS:
            if not any(essential in name for name in section_names):
                missing.append(f"Missing {essential} section")

        return missing

    def _generate_suggestions(
        self,
        sections: List[CardSection],
        missing_elements: List[str],
        weaknesses: List[str],
        content: str,
    ) -> List[str]:
        """Generate specific improvement suggestions."""
        suggestions = []

        # Address missing elements
        for element in missing_elements:
            if "description" in element.lower():
                suggestions.append("Add a clear description section explaining what this dataset/model is and its purpose")
            elif "structure" in element.lower():
                suggestions.append("Document the dataset structure including file formats, columns, and data types")
            elif "usage" in element.lower():
                suggestions.append("Provide usage examples with code snippets showing how to load and use the data")
            elif "license" in element.lower():
                suggestions.append("Clearly state the license under which this dataset/model is released")
            elif "citation" in element.lower():
                suggestions.append("Add citation information in BibTeX format for academic use")
            elif "limitation" in element.lower():
                suggestions.append("Discuss known limitations, biases, and appropriate use cases")

        # Address weaknesses
        if "too brief" in str(weaknesses):
            suggestions.append("Expand documentation to at least 1000 words for better clarity")

        if "no code examples" in str(weaknesses).lower():
            suggestions.append("Add Python code examples showing data loading and basic operations")

        # Compare with gold standards
        if self.gold_standards:
            gold_example = list(self.gold_standards.values())[0]
            gold_sections = [s.name for s in gold_example.sections]
            current_sections = [s.name for s in sections]

            missing_from_gold = set(gold_sections) - set(current_sections)
            if missing_from_gold:
                suggestions.append(f"Consider adding sections like: {', '.join(list(missing_from_gold)[:3])}")

        # Specific suggestions based on content analysis
        if len(content) < 300:
            suggestions.append("This card is extremely brief (like arcinstitute/opengenome2). Aim for comprehensive documentation like tahoebio/Tahoe-100M")

        if not re.search(r"```python[\s\S]*?```", content):
            suggestions.append("Add Python code blocks with practical examples")

        if not re.search(r"@\w+", content) and "model" not in content.lower():
            suggestions.append("Include academic citations if this is published research")

        return suggestions

    def compare_with_baselines(
        self,
        repo_id: str,
        repo_type: str = "dataset"
    ) -> Dict[str, Any]:
        """Compare a repository with baseline examples.

        Args:
            repo_id: Repository to analyze
            repo_type: Type of repository

        Returns:
            Detailed comparison with baselines
        """
        # Analyze the target repository
        target_analysis = self.analyze_card(repo_id, repo_type)

        # Compare with gold standards
        gold_comparison = {}
        for gold_id, gold_analysis in self.gold_standards.items():
            gold_comparison[gold_id] = {
                "quality_gap": gold_analysis.quality_score - target_analysis.quality_score,
                "missing_sections": [
                    s.name for s in gold_analysis.sections
                    if s.name not in [ts.name for ts in target_analysis.sections]
                ],
                "length_difference": gold_analysis.total_length - target_analysis.total_length,
            }

        # Compare with poor examples
        poor_comparison = {}
        for poor_id, poor_analysis in self.poor_examples.items():
            poor_comparison[poor_id] = {
                "quality_difference": target_analysis.quality_score - poor_analysis.quality_score,
                "improvements": [
                    s for s in target_analysis.strengths
                    if s not in poor_analysis.strengths
                ],
            }

        # Generate specific recommendations
        recommendations = self._generate_recommendations(
            target_analysis,
            gold_comparison,
            poor_comparison
        )

        return {
            "target_analysis": target_analysis.to_dict(),
            "comparison_with_gold_standards": gold_comparison,
            "comparison_with_poor_examples": poor_comparison,
            "recommendations": recommendations,
            "estimated_improvement_impact": self._estimate_improvement_impact(
                target_analysis,
                gold_comparison
            ),
        }

    def _generate_recommendations(
        self,
        target: CardAnalysis,
        gold_comparison: Dict[str, Any],
        poor_comparison: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations."""
        recommendations = []

        # Find the closest gold standard
        best_gold = min(
            gold_comparison.items(),
            key=lambda x: abs(x[1]["quality_gap"])
        )

        # High priority: Missing essential sections
        for section in best_gold[1]["missing_sections"]:
            if section.lower() in [s.lower() for s in self.ESSENTIAL_SECTIONS]:
                recommendations.append({
                    "priority": "HIGH",
                    "action": f"Add {section} section",
                    "reference": f"See {best_gold[0]} for example",
                    "impact": "Essential for documentation completeness",
                })

        # Medium priority: Content improvements
        if target.total_length < 1000:
            recommendations.append({
                "priority": "MEDIUM",
                "action": "Expand documentation significantly",
                "reference": f"Target length similar to tahoebio/Tahoe-100M (~{self.gold_standards.get('tahoebio/Tahoe-100M', target).total_length} chars)",
                "impact": "Improves clarity and usability",
            })

        # Add code examples if missing
        if not any(s.has_code_examples for s in target.sections):
            recommendations.append({
                "priority": "HIGH",
                "action": "Add code examples for data loading and usage",
                "reference": "Follow tahoebio/Tahoe-100M example structure",
                "impact": "Critical for user adoption",
            })

        return recommendations

    def _estimate_improvement_impact(
        self,
        target: CardAnalysis,
        gold_comparison: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Estimate the impact of implementing improvements."""
        # Calculate potential score improvement
        best_gold_score = max(
            self.gold_standards.values(),
            key=lambda x: x.quality_score
        ).quality_score

        potential_improvement = best_gold_score - target.quality_score

        return {
            "current_score": target.quality_score,
            "potential_score": min(100, target.quality_score + potential_improvement * 0.7),
            "estimated_improvement": f"{potential_improvement * 0.7:.1f} points",
            "percentile_change": self._estimate_percentile_change(target.quality_score),
        }

    def _estimate_percentile_change(self, current_score: float) -> str:
        """Estimate percentile ranking change."""
        if current_score < 20:
            return "From bottom 10% to top 50%"
        elif current_score < 40:
            return "From bottom 30% to top 30%"
        elif current_score < 60:
            return "From average to top 20%"
        else:
            return "From good to excellent (top 10%)"

    def generate_improvement_report(
        self,
        repo_id: str,
        repo_type: str = "dataset",
        output_format: str = "markdown",
    ) -> str:
        """Generate a comprehensive improvement report.

        Args:
            repo_id: Repository to analyze
            repo_type: Type of repository
            output_format: Format of report (markdown or json)

        Returns:
            Formatted improvement report
        """
        comparison = self.compare_with_baselines(repo_id, repo_type)

        if output_format == "json":
            import json
            return json.dumps(comparison, indent=2)

        # Generate markdown report
        report = f"""# Dataset Card Improvement Report

## Repository: {repo_id}

Generated: {datetime.utcnow().isoformat()}

## Current Status

- **Quality Score**: {comparison['target_analysis']['quality_score']:.1f}/100
- **Documentation Length**: {comparison['target_analysis']['total_length']} characters
- **Number of Sections**: {len(comparison['target_analysis']['sections'])}

## Comparison with Gold Standards

### Compared to tahoebio/Tahoe-100M (Excellent Example)
"""

        if "tahoebio/Tahoe-100M" in comparison["comparison_with_gold_standards"]:
            gold = comparison["comparison_with_gold_standards"]["tahoebio/Tahoe-100M"]
            report += f"""
- Quality gap: {gold['quality_gap']:.1f} points
- Missing sections: {', '.join(gold['missing_sections']) if gold['missing_sections'] else 'None'}
- Length difference: {gold['length_difference']:,} characters
"""

        report += """
### Compared to arcinstitute/opengenome2 (Poor Example)
"""

        if "arcinstitute/opengenome2" in comparison["comparison_with_poor_examples"]:
            poor = comparison["comparison_with_poor_examples"]["arcinstitute/opengenome2"]
            report += f"""
- Quality advantage: {poor['quality_difference']:.1f} points
- Improvements made: {', '.join(poor['improvements']) if poor['improvements'] else 'None'}
"""

        report += """
## Strengths

"""
        for strength in comparison["target_analysis"]["strengths"]:
            report += f"- {strength}\n"

        report += """
## Weaknesses

"""
        for weakness in comparison["target_analysis"]["weaknesses"]:
            report += f"- {weakness}\n"

        report += """
## Priority Improvements

"""
        for i, rec in enumerate(comparison["recommendations"], 1):
            emoji = "HIGH" if rec["priority"] == "HIGH" else "MEDIUM"
            report += f"""
{i}. {emoji} **{rec['action']}**
   - Reference: {rec['reference']}
   - Impact: {rec['impact']}
"""

        report += f"""
## Estimated Impact

Implementing these improvements could:
- Increase quality score from {comparison['estimated_improvement_impact']['current_score']:.1f} to {comparison['estimated_improvement_impact']['potential_score']:.1f}
- {comparison['estimated_improvement_impact']['percentile_change']}

## Next Steps

1. Review this report with your team
2. Prioritize HIGH priority improvements
3. Use the reference examples as templates
4. Test changes locally before submitting
5. **Never auto-push changes - always review manually**

---
*Report generated by Science Card Improvement Toolkit*
"""

        return report