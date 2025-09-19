# Science Dataset & Model Card Improvement Project

A comprehensive toolkit for discovering, assessing, and improving dataset and model cards on Hugging Face, with a focus on scientific datasets and models.

## ��� Project Goals

- **Discover** science-related datasets and models on Hugging Face that need better documentation
- **Assess** card quality using automated scoring and manual review
- **Generate** high-quality, informative dataset and model cards
- **Tag** repositories with appropriate tags (`huggingscience`, `science`, domain-specific tags)
- **Contribute** improvements via automated PRs and community collaboration

## ��� Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up your Hugging Face token
export HF_TOKEN="your_token_here"

# Run discovery to find science datasets
python scripts/discover_science_repos.py --type dataset --limit 100

# Assess card quality
python scripts/assess_card_quality.py --repo-id arcinstitute/opengenome2

# Generate improved card
python scripts/generate_card.py --repo-id arcinstitute/opengenome2 --type dataset

# Create PR with improvements
python scripts/create_pr.py --repo-id arcinstitute/opengenome2 --card-file improved_card.md
```

## ��� Repository Structure

```
├── scripts/                    # Main automation scripts
│   ├── discover_science_repos.py    # Find science datasets/models
│   ├── assess_card_quality.py       # Score existing cards
│   ├── generate_card.py             # Generate improved cards
│   ├── create_pr.py                # Create PRs with improvements
│   └── manage_tags.py               # Suggest and apply tags
├── templates/                  # Card templates
│   ├── dataset_card_template.md     # Comprehensive dataset card
│   ├── model_card_template.md       # Comprehensive model card
│   └── minimal_card_template.md     # Minimal viable card
├── examples/                   # Example cards and outputs
│   ├── good_examples/              # High-quality card examples
│   └── bad_examples/               # Cards that need improvement
├── utils/                      # Utility functions
│   ├── hf_api.py                   # Hugging Face API helpers
│   ├── card_scorer.py              # Card quality assessment
│   └── template_engine.py          # Card generation engine
├── config/                     # Configuration files
│   ├── science_keywords.json       # Science-related search terms
│   ├── domain_tags.json            # Domain-specific tags
│   └── scoring_criteria.json       # Card scoring parameters
└── docs/                       # Documentation
    ├── card_guidelines.md           # How to write good cards
    ├── api_reference.md             # API documentation
    └── contributing.md              # How to contribute
```

## ��� Discovery Process

### 1. Automated Discovery
- Search using science-related keywords
- Filter by repository type (dataset/model)
- Collect metadata and basic information

### 2. Quality Assessment
- **Missing README**: No README.md file
- **Short README**: Less than 300 characters
- **Missing sections**: License, citation, data collection, limitations
- **Dataset viewer errors**: Generation errors, loading issues
- **Poor tagging**: Missing domain-specific tags

### 3. Scoring System
- **Score 0-2**: Critical issues (missing README, major errors)
- **Score 3-5**: Needs improvement (short README, missing sections)
- **Score 6-8**: Good but could be enhanced
- **Score 9-10**: Excellent card

## ��� Card Templates

### Dataset Card Template
- **Title & Description**: Clear, concise summary
- **Motivation**: Why this dataset was created
- **Data Sources**: Collection methods, sources, access
- **Structure**: Splits, columns, sizes, sample data
- **License**: Clear licensing information
- **Citation**: Proper academic citation format
- **Usage Examples**: Code snippets, loading instructions
- **Limitations**: Known issues, biases, ethical considerations
- **Contact**: Maintainer information

### Model Card Template
- **Model Description**: Architecture, purpose, capabilities
- **Training Data**: Dataset used, preprocessing
- **Training Procedure**: Hyperparameters, training setup
- **Evaluation**: Metrics, benchmarks, performance
- **Limitations**: Known issues, biases, use cases to avoid
- **Citation**: Proper academic citation
- **License**: Model licensing information

## ���️ Tagging Strategy

### Core Tags
- `huggingscience`: Main project tag
- `science`: General science tag
- `datasets`: For datasets
- `models`: For models

### Domain-Specific Tags
- **Biology**: `biology`, `genomics`, `proteomics`, `single-cell`
- **Chemistry**: `chemistry`, `molecular`, `drug-discovery`
- **Physics**: `physics`, `astronomy`, `quantum`
- **Medicine**: `medical`, `clinical`, `healthcare`
- **Environment**: `climate`, `ecology`, `environmental`

## ��� Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Run** the discovery scripts to find repositories
4. **Assess** card quality and generate improvements
5. **Submit** PRs with your improvements
6. **Coordinate** with maintainers for merging

## ��� Example Workflow

```python
from utils.hf_api import HFApiClient
from utils.card_scorer import CardScorer
from utils.template_engine import CardGenerator

# Initialize clients
api = HFApiClient()
scorer = CardScorer()
generator = CardGenerator()

# Find science datasets
datasets = api.search_science_repos(type="dataset", limit=50)

# Assess quality
for dataset in datasets:
    score = scorer.assess_card(dataset.id)
    if score < 6:  # Needs improvement
        # Generate improved card
        new_card = generator.generate_dataset_card(dataset.id)
        
        # Create PR
        pr_url = api.create_pr(
            repo_id=dataset.id,
            file_path="README.md",
            content=new_card,
            message="Improve dataset card quality"
        )
        print(f"Created PR for {dataset.id}: {pr_url}")
```

## ��� Success Metrics

- **Cards Improved**: Number of repositories with enhanced cards
- **PRs Merged**: Successful contributions to the community
- **Tags Applied**: Proper tagging of science repositories
- **Community Engagement**: Discussions and collaborations

## ��� Resources

- [Hugging Face Dataset Card Guide](https://huggingface.co/docs/datasets/en/dataset_card)
- [Hugging Face Model Card Guide](https://huggingface.co/docs/hub/model-cards)
- [Example: Poor Card (Arc Institute)](https://huggingface.co/datasets/arcinstitute/opengenome2)
- [Example: Good Card (Tahoe-100M)](https://huggingface.co/datasets/tahoebio/Tahoe-100M)

## ⚠️ Important Notes

- **Respect maintainers**: Always coordinate with repository maintainers
- **Quality over quantity**: Focus on meaningful improvements
- **Community guidelines**: Follow Hugging Face community standards
- **Attribution**: Properly credit original authors and sources

## ��� License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ��� Getting Started

To get started with this project:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/VontariusF/science-card-improvement.git
   cd science-card-improvement
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your Hugging Face token**:
   ```bash
   export HF_TOKEN="your_token_here"
   ```

4. **Run the discovery script**:
   ```bash
   python scripts/discover_science_repos.py --type dataset --limit 10 --display
   ```

5. **Start contributing** to improve science dataset and model cards!

## ��� Support

For questions, issues, or contributions:

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share ideas
- **Documentation**: Comprehensive guides and API reference
- **Examples**: Working examples and use cases

---

**This project aims to make scientific datasets and models more accessible and usable for the research community by improving their documentation and discoverability.**
