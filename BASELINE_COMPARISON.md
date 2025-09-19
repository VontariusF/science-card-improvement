# Baseline Comparison System

## Overview

The Science Card Improvement toolkit uses a sophisticated baseline comparison system that learns from exemplary and poor documentation examples to provide intelligent improvement suggestions. **All changes require human review and confirmation before any submission.**

## Reference Baselines

### Gold Standard Examples (A+ Quality)
- **[tahoebio/Tahoe-100M](https://huggingface.co/datasets/tahoebio/Tahoe-100M)** - Exemplary dataset card with comprehensive documentation
- **[bigscience/bloom](https://huggingface.co/models/bigscience/bloom)** - Excellent model card example
- **[allenai/olmo](https://huggingface.co/models/allenai/olmo)** - Comprehensive documentation standard

### Poor Examples (Needs Improvement)
- **[arcinstitute/opengenome2](https://huggingface.co/datasets/arcinstitute/opengenome2)** - Bone dry dataset card that needs significant improvement

## How It Works

### 1. Baseline Analysis
The system first analyzes both good and bad examples to understand:
- What makes a card excellent
- Common patterns in poor documentation
- Essential vs. nice-to-have sections
- Quality indicators (code examples, citations, etc.)

### 2. Target Repository Analysis
When analyzing a new repository, the system:
```python
# Automatic comparison with baselines
analyzer = BaselineAnalyzer()
comparison = analyzer.compare_with_baselines("your-org/your-dataset")
```

### 3. Gap Analysis
The system identifies:
- **Missing sections** compared to gold standards
- **Quality gaps** in existing sections
- **Length differences** and content depth
- **Specific improvements** needed

### 4. Improvement Generation
Based on the analysis, the system:
- Generates specific, actionable suggestions
- Prioritizes improvements (HIGH/MEDIUM/LOW)
- Provides references to gold standard examples
- Estimates impact of improvements

### 5. Human Review (REQUIRED)
**Critical: No changes are ever pushed automatically!**
```python
# All proposals must be reviewed
review_system = HumanReviewSystem()
proposal = review_system.create_proposal(
    repo_id="your-org/your-dataset",
    proposed_content=improved_card,
    improvements=["Added usage examples", "Added citations"],
)

# Interactive review required
approved = review_system.review_proposal(proposal, interactive=True)

# Only creates a draft, never auto-submits
if approved:
    pr_draft = review_system.create_pr_draft(proposal)
    # Manual submission required
```

## Quality Scoring System

The system scores cards on a 0-100 scale based on:

| Component | Weight | Criteria |
|-----------|--------|----------|
| **Length** | 20% | Comprehensive documentation (>2000 chars optimal) |
| **Essential Sections** | 40% | Description, structure, usage, license, citation |
| **Content Quality** | 30% | Code examples, citations, visual aids |
| **Special Features** | 10% | Ethical considerations, limitations, changelog |

### Score Interpretation
- **0-20**: Critical issues (like arcinstitute/opengenome2)
- **21-40**: Needs significant improvement
- **41-60**: Acceptable but could be enhanced
- **61-80**: Good documentation
- **81-100**: Excellent (like tahoebio/Tahoe-100M)

## Safety Features

### Never Auto-Push
The system includes multiple safeguards:
1. **No automatic PR creation** - All PRs require explicit confirmation
2. **Human review required** - Interactive review for every change
3. **Dry-run mode** - Test changes without any submissions
4. **Audit trail** - All proposals saved with timestamps

### Review Process
```bash
# Review all pending proposals
sci-review --interactive

# For each proposal, you can:
# A - Approve (still requires manual PR submission)
# E - Edit the proposed content
# R - Reject with reason
# S - Skip for later
# V - View full content
# D - Download for external review
```

## Configuration

### Required Environment Variables
```bash
# Hugging Face token (required for private repos)
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxx"

# Disable auto-suggestions (extra safety)
export AUTO_SUGGEST=false

# Force dry-run mode
export SUBMISSION_DRY_RUN=true

# Set review requirement
export REQUIRE_HUMAN_REVIEW=true  # Always true by default
```

### Optional Configuration
```bash
# Baseline repositories (can be customized)
export GOLD_STANDARD_REPOS="tahoebio/Tahoe-100M,bigscience/bloom"
export POOR_EXAMPLE_REPOS="arcinstitute/opengenome2"

# Quality thresholds
export MIN_QUALITY_SCORE=60  # Minimum acceptable score
export TARGET_QUALITY_SCORE=80  # Target for improvements

# Review settings
export INTERACTIVE_REVIEW=true  # Force interactive mode
export EXPORT_PROPOSALS=true  # Save all proposals to disk
```

## Typical Workflow

### Step 1: Analyze Repository
```bash
# Analyze and compare with baselines
sci-analyze --repo-id arcinstitute/opengenome2 --output analysis.md
```

### Step 2: Generate Improvements
```bash
# Generate improved card based on analysis
sci-generate --repo-id arcinstitute/opengenome2 \
             --baseline tahoebio/Tahoe-100M \
             --output improved_card.md
```

### Step 3: Review Changes
```bash
# Interactive review (REQUIRED)
sci-review --repo-id arcinstitute/opengenome2 \
           --proposed-file improved_card.md
```

### Step 4: Create PR Draft
```bash
# Creates draft only - no automatic submission
sci-draft --repo-id arcinstitute/opengenome2 \
          --approved-proposal proposal_123.json
```

### Step 5: Manual Submission
```bash
# Explicitly submit after final review
sci-submit --draft-file pr_draft_123.json \
           --confirm  # Still asks for confirmation
```

## Comparison Report Example

When comparing a repository with baselines, you get:

```markdown
# Comparison Report: arcinstitute/opengenome2

## Current Status
- Quality Score: 15.2/100 (Critical)
- Length: 238 characters (Far below standard)
- Sections: 2 (Missing most essential sections)

## Gap Analysis vs. tahoebio/Tahoe-100M
- Quality Gap: -73.8 points
- Missing Sections: Usage, Data Structure, License, Citation, Limitations
- Length Difference: -15,762 characters

## Priority Improvements
1. HIGH: Add comprehensive description section
2. HIGH: Include usage examples with code
3. HIGH: Add license and citation information
4. MEDIUM: Document dataset structure
5. MEDIUM: Add data collection methodology

## Estimated Impact
- Current percentile: Bottom 10%
- Post-improvement: Top 30%
- Quality score increase: +45-60 points
```

## Important Notes

1. **Human Review is Mandatory**: The system will never bypass human review
2. **No Auto-Push**: Changes are never automatically pushed to repositories
3. **Respect Maintainers**: Always coordinate with repository maintainers
4. **Quality Over Quantity**: Focus on meaningful improvements
5. **Test Locally First**: Always test changes before submission

## Monitoring & Auditing

All actions are logged and audited:
- Proposals saved to `output/proposals/`
- Review decisions logged with timestamps
- PR drafts saved separately from submissions
- Complete audit trail for compliance

## Additional Resources

- [Hugging Face Dataset Card Guide](https://huggingface.co/docs/datasets/en/dataset_card)
- [Model Card Best Practices](https://huggingface.co/docs/hub/model-cards)
- [Gold Standard Example](https://huggingface.co/datasets/tahoebio/Tahoe-100M)
- [Poor Example to Learn From](https://huggingface.co/datasets/arcinstitute/opengenome2)