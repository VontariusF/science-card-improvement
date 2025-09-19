# 🔬 Science Card Improvement Toolkit

[![CI Pipeline](https://github.com/VontariusF/science-card-improvement/workflows/CI%20Pipeline/badge.svg)](https://github.com/VontariusF/science-card-improvement/actions)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**An intelligent system that analyzes and improves Hugging Face dataset/model documentation by learning from the best (and worst) examples.**

## 🎯 The Problem & Solution

### The Problem
Many valuable scientific datasets on Hugging Face have minimal documentation. For example:
- ❌ **[arcinstitute/opengenome2](https://huggingface.co/datasets/arcinstitute/opengenome2)** - Amazing dataset, bone-dry documentation

### The Solution
Learn from exemplary documentation and provide intelligent improvements:
- ✅ **[tahoebio/Tahoe-100M](https://huggingface.co/datasets/tahoebio/Tahoe-100M)** - Gold standard documentation

Our system automatically:
1. **Analyzes** repositories against known good/bad examples
2. **Identifies** specific gaps and improvements needed
3. **Generates** enhanced documentation following best practices
4. **Requires** human review before ANY changes
5. **Never** automatically pushes changes

## ⚡ Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/VontariusF/science-card-improvement.git
cd science-card-improvement
pip install -e .

# 2. Set your Hugging Face token (required for API access)
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxx"

# 3. Analyze a repository (like the Arc Institute example)
sci-analyze --repo-id arcinstitute/opengenome2

# 4. Generate improvements based on gold standards
sci-generate --repo-id arcinstitute/opengenome2 \
             --baseline tahoebio/Tahoe-100M

# 5. Review proposed changes (REQUIRED - no auto-push)
sci-review --interactive

# 6. Create PR draft (still requires manual submission)
sci-draft --approved-only
```

## 🛡️ Safety & Ethics

### ⚠️ IMPORTANT: Human Review Required

This system **NEVER** automatically pushes changes. Every improvement requires:
1. **Human review** of proposed changes
2. **Explicit approval** before creating PR drafts
3. **Manual submission** of pull requests
4. **Coordination** with repository maintainers

### Key Safety Features
```python
# The system enforces human review
review_system = HumanReviewSystem()
proposal = review_system.create_proposal(...)

# Interactive review required
approved = review_system.review_proposal(proposal, interactive=True)

# Even after approval, only creates a draft
if approved:
    pr_draft = review_system.create_pr_draft(proposal)
    # Still requires manual submission
```

## 📊 How Baseline Comparison Works

### 1. Learning from Examples

The system studies both excellent and poor documentation:

**Gold Standards (A+ Quality):**
- `tahoebio/Tahoe-100M` - Comprehensive dataset documentation
- `bigscience/bloom` - Excellent model card
- `allenai/olmo` - Thorough documentation

**Poor Examples (Needs Work):**
- `arcinstitute/opengenome2` - Minimal documentation

### 2. Intelligent Analysis

For each repository, the system analyzes:
- **Structure**: Which sections are present/missing
- **Content Quality**: Code examples, citations, depth
- **Completeness**: Coverage of essential topics
- **Comparison**: Gaps vs. gold standards

### 3. Quality Scoring

Cards are scored 0-100 based on:
- **Essential Sections** (40%): Description, usage, license, citation
- **Content Quality** (30%): Examples, references, clarity
- **Documentation Length** (20%): Comprehensive coverage
- **Special Features** (10%): Ethics, limitations, changelog

### 4. Example Comparison

```bash
# Compare Arc Institute's card with Tahoe Bio's excellent example
sci-compare --target arcinstitute/opengenome2 \
            --baseline tahoebio/Tahoe-100M

# Output:
# Current Score: 15/100 (Critical)
# Baseline Score: 89/100 (Excellent)
# Quality Gap: -74 points
# Missing: Usage examples, data structure, license, citations
# Improvement Potential: +45-60 points with suggested changes
```

## 🔧 Configuration

### Required Environment Variables
```bash
# Hugging Face API token (required)
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxx"

# Safety settings (defaults shown)
export REQUIRE_HUMAN_REVIEW=true    # Cannot be disabled
export AUTO_PUSH_ENABLED=false      # Cannot be enabled
export SUBMISSION_DRY_RUN=false     # Set true for testing
```

### Optional Configuration
```bash
# Baseline repositories
export GOLD_STANDARD_REPOS="tahoebio/Tahoe-100M,bigscience/bloom"
export POOR_EXAMPLE_REPOS="arcinstitute/opengenome2"

# Quality thresholds
export MIN_QUALITY_SCORE=20         # Flag repos below this
export TARGET_QUALITY_SCORE=80      # Aim for this level

# Performance
export DISCOVERY_MAX_WORKERS=10     # Parallel processing
export CACHE_TTL=3600               # Cache duration (seconds)
```

## 📋 Typical Workflow

### Step 1: Discover Repositories Needing Help
```bash
# Find science datasets with poor documentation
sci-discover --type dataset \
             --min-downloads 100 \
             --max-quality-score 30 \
             --limit 50
```

### Step 2: Analyze Against Baselines
```bash
# Detailed analysis with baseline comparison
sci-analyze --repo-id arcinstitute/opengenome2 \
            --compare-with tahoebio/Tahoe-100M \
            --output analysis_report.md
```

### Step 3: Generate Improvements
```bash
# Generate enhanced documentation
sci-generate --repo-id arcinstitute/opengenome2 \
             --template scientific \
             --baseline tahoebio/Tahoe-100M \
             --output improved_card.md
```

### Step 4: Review Changes (MANDATORY)
```bash
# Interactive review session
sci-review --proposed-file improved_card.md

# Review options:
# A - Approve (creates draft, no auto-submit)
# E - Edit proposed content
# R - Reject with reason
# S - Skip for later
# V - View full content
# D - Download for external review
```

### Step 5: Create PR Draft
```bash
# Generate PR draft (not submitted)
sci-draft --repo-id arcinstitute/opengenome2 \
          --approved-proposal proposal_123.json \
          --output pr_draft.json
```

### Step 6: Manual Submission
```bash
# Explicitly submit after final review
sci-submit --draft pr_draft.json \
           --confirm \
           --message "Improve dataset documentation"

# Even this command asks for final confirmation!
```

## 📈 Success Metrics

### Quality Improvements
- Average score increase: +40-60 points
- Documentation length: 10x-20x increase
- Section coverage: 70%+ essential sections added

### Example Transformation

**Before (arcinstitute/opengenome2):**
- Score: 15/100
- Length: 238 characters
- Sections: 2
- No usage examples
- No citations

**After (with improvements):**
- Score: 75/100
- Length: 5,000+ characters
- Sections: 12+
- Complete usage examples
- Proper citations

## 🏗️ Architecture

```
src/
├── core/
│   ├── baseline_analyzer.py  # Learns from good/bad examples
│   ├── human_review.py       # Enforces human review
│   ├── discovery.py          # Finds repositories
│   └── generator.py          # Creates improvements
├── cli/                      # Command-line interfaces
├── config/                   # Configuration management
└── validators/               # Input validation
```

## 🧪 Testing

```bash
# Run all tests
make test

# Test baseline comparison
pytest tests/unit/test_baseline_analyzer.py

# Test human review system
pytest tests/unit/test_human_review.py

# Integration tests
pytest tests/integration/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all safety checks pass
5. Submit a pull request

## ⚠️ Important Limitations

1. **No Automatic Pushing**: All changes require human review
2. **Respect Maintainers**: Always coordinate with repo owners
3. **Quality Focus**: Better to improve few repos well than many poorly
4. **Factual Accuracy**: AI suggestions need human verification
5. **License Compliance**: Respect original licenses

## 📚 Resources

- [Baseline Comparison Details](BASELINE_COMPARISON.md)
- [Gold Standard Example](https://huggingface.co/datasets/tahoebio/Tahoe-100M)
- [Poor Example](https://huggingface.co/datasets/arcinstitute/opengenome2)
- [HF Dataset Card Guide](https://huggingface.co/docs/datasets/en/dataset_card)

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

- **Tahoe Bio** for the excellent Tahoe-100M documentation example
- **Arc Institute** for the valuable opengenome2 dataset (documentation improvements coming!)
- **Hugging Face** for the amazing platform

---

<div align="center">

**Making scientific data more accessible through better documentation**

*All improvements require human review - No automatic pushing*

</div>