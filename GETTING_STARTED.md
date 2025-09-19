# Getting Started Guide

This guide will help you get up and running with the Science Card Improvement Project.

## Prerequisites

- Python 3.8 or higher
- Git
- Hugging Face account with API token
- Basic knowledge of Python and command-line tools

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/VontariusF/science-card-improvement.git
cd science-card-improvement
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Required
HF_TOKEN=your_huggingface_token_here

# Optional
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

Or set the environment variable directly:

```bash
export HF_TOKEN="your_token_here"
```

## Quick Start

### 1. Discover Science Repositories

```bash
# Find science datasets
python scripts/discover_science_repos.py --type dataset --limit 10 --display

# Find science models
python scripts/discover_science_repos.py --type model --limit 10 --display

# Find both types
python scripts/discover_science_repos.py --type both --limit 20 --display
```

### 2. Assess Card Quality

```bash
# Assess a specific repository
python scripts/assess_card_quality.py --repo-id arcinstitute/opengenome2 --detailed

# Assess and save results
python scripts/assess_card_quality.py --repo-id tahoebio/Tahoe-100M --output assessment.json
```

### 3. Generate Improved Cards

```bash
# Generate comprehensive card
python scripts/generate_card.py --repo-id arcinstitute/opengenome2 --type dataset

# Generate minimal card
python scripts/generate_card.py --repo-id microsoft/DialoGPT-medium --type model --template minimal

# Preview generated card
python scripts/generate_card.py --repo-id tahoebio/Tahoe-100M --preview
```

### 4. Create Pull Requests

```bash
# Create PR with improved card
python scripts/create_pr.py create --repo-id arcinstitute/opengenome2 --card-file improved_card.md

# Create PR with custom title
python scripts/create_pr.py create --repo-id tahoebio/Tahoe-100M --card-file card.md --title "Improve documentation"

# List all PRs
python scripts/create_pr.py manage --list --stats
```

### 5. Manage Tags

```bash
# Suggest tags for repository
python scripts/manage_tags.py --repo-id arcinstitute/opengenome2 --suggest

# Apply specific tags
python scripts/manage_tags.py --repo-id tahoebio/Tahoe-100M --apply --tags "biology,genomics,huggingscience"

# Bulk suggest tags
python scripts/manage_tags.py --bulk-suggest --input discovery_results.json --output tag_suggestions.json
```

## Example Workflow

Here's a complete example of how to use the project:

```bash
# 1. Discover science datasets
python scripts/discover_science_repos.py --type dataset --limit 50 --output my_discovery.json

# 2. Assess quality of discovered repositories
python scripts/assess_card_quality.py --repo-id arcinstitute/opengenome2 --detailed

# 3. Generate improved card
python scripts/generate_card.py --repo-id arcinstitute/opengenome2 --type dataset --preview

# 4. Create PR with improvements
python scripts/create_pr.py create --repo-id arcinstitute/opengenome2 --card-file arcinstitute_opengenome2_improved_card.md

# 5. Suggest tags
python scripts/manage_tags.py --repo-id arcinstitute/opengenome2 --suggest
```

## Configuration

### Science Keywords

The project uses comprehensive keyword lists organized by domain. You can customize these in `config/science_keywords.json`:

```json
[
  "science", "biology", "genomics", "proteomics", "chemistry", 
  "physics", "astronomy", "medicine", "medical", "clinical",
  "healthcare", "drug", "molecular", "single-cell", "bioinformatics"
]
```

### Domain Tags

Domain-specific tags are defined in `config/domain_tags.json`:

```json
{
  "biology": [
    "biology", "genomics", "proteomics", "single-cell", "bioinformatics"
  ],
  "chemistry": [
    "chemistry", "molecular", "drug-discovery", "pharmaceutical"
  ],
  "physics": [
    "physics", "astronomy", "astrophysics", "quantum", "nuclear"
  ]
}
```

## Troubleshooting

### Common Issues

1. **HF_TOKEN not set**
   ```
   Error: HF_TOKEN environment variable not set
   ```
   Solution: Set your Hugging Face token as described in the installation section.

2. **Permission denied errors**
   ```
   Error: Could not access repository
   ```
   Solution: Ensure the repository is publicly accessible and you have the correct permissions.

3. **Import errors**
   ```
   ModuleNotFoundError: No module named 'huggingface_hub'
   ```
   Solution: Install dependencies with `pip install -r requirements.txt`

### Getting Help

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share ideas
- **Documentation**: Check the docs/ directory for detailed guides

## Next Steps

1. **Explore the examples** in the `examples/` directory
2. **Read the documentation** in the `docs/` directory
3. **Try the discovery script** with different parameters
4. **Contribute improvements** by submitting pull requests
5. **Share your results** with the community

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

---

Happy improving! íº€
