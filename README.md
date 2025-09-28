# Science Card Improvement Toolkit

**An intelligent system that discovers and improves Hugging Face dataset/model documentation by learning from exemplary examples.**

## 🚀 Quick Start (Essential Components Only)

### 1. Install Dependencies
```bash
# Install the package
pip install -e .

# Set your Hugging Face token
export HF_TOKEN="your_token_here"
```

### 2. Run Discovery
```bash
# Quick discovery of datasets needing improvement
python find_datasets.py

# Or use the CLI for more control
python -m src.cli.discover --limit 200 --verbose
```

### 3. Analyze Specific Repository
```bash
# Compare with baseline examples
python -m src.cli.compare --target arcinstitute/opengenome2 --baseline tahoebio/Tahoe-100M

# Analyze specific repository
python -m src.cli.compare analyze --repo-id arcinstitute/opengenome2
```

## 📋 Essential Components (Required)

### Core Files
- **`pyproject.toml`** - Package configuration and dependencies
- **`requirements.txt`** - Minimal dependencies (huggingface_hub)
- **`.env`** - Your Hugging Face credentials
- **`find_datasets.py`** - Main discovery script

### Source Code (Essential)
```
src/science_card_improvement/
├── cli/
│   ├── discover.py          # Discovery CLI
│   └── compare.py           # Analysis CLI
├── config/
│   └── settings.py          # Configuration management
├── resources/
│   └── science_keywords.json # 192 science keywords
├── discovery/
│   └── repository.py        # Repository discovery logic
├── analysis/
│   └── baseline.py          # Baseline analysis
└── utils/
    ├── cache.py             # Caching utilities
    └── logger.py            # Logging utilities
```

### Configuration Files
- **`src/science_card_improvement/resources/science_keywords.json`** - 192 comprehensive science keywords
- **`src/science_card_improvement/config/settings.py`** - Environment variable handling

## ❌ Unnecessary Components (Can Be Removed)

### Documentation Files
- `README_ENHANCED.md` - Redundant documentation
- `BASELINE_COMPARISON.md` - Detailed docs (not needed for basic usage)
- `GETTING_STARTED.md` - Redundant with this README
- `docs/` - Entire directory (optional documentation)

### Development Files
- `tests/` - Entire directory (development only)
- `Makefile` - Development automation
- `Dockerfile` & `docker-compose.yml` - Containerization (optional)
- `.github/workflows/` - CI/CD (development only)

### Generated/Cache Files
- `.cache/` - Runtime cache (auto-generated)
- `logs/` - Log files (auto-generated)
- `output/` - Output files (auto-generated)
- `*.egg-info/` - Python package metadata (auto-generated)
- `__pycache__/` - Python bytecode cache (auto-generated)

### Example Files
- `examples/` - Example files (optional)
- `templates/` - Card templates (optional for basic usage)

### Scripts Directory
- `scripts/discover_science_repos.py` - Old script (replaced by CLI)

## 🛠️ Installation

### Minimal Installation
```bash
# Clone repository
git clone https://github.com/VontariusF/science-card-improvement.git
cd science-card-improvement

# Install in development mode
pip install -e .

# Set up environment
cp .env.example .env
# Edit .env and add your HF_TOKEN
```

### Dependencies (Auto-installed)
The system automatically installs these essential dependencies:
- `huggingface-hub>=0.19.0` - Hugging Face API
- `click>=8.0.0` - CLI framework
- `rich>=13.0.0` - Rich terminal output
- `pydantic>=2.0.0` - Data validation
- `python-dotenv>=1.0.0` - Environment variables

## 🎯 Core Functionality

### 1. Discovery System
**192 Science Keywords** covering all major scientific domains:
- **Medical Sciences**: clinical, pathology, oncology, immunology, pharmacology
- **Life Sciences**: genomics, proteomics, cell biology, molecular biology
- **Physical Sciences**: physics, chemistry, materials science, nanotechnology
- **Earth Sciences**: geology, climate, oceanography, environmental science
- **Specialized Fields**: neuroscience, bioinformatics, forensic science

**Performance**: Discovers 200+ science datasets in ~30 seconds with intelligent parallel processing.

### 2. Quality Assessment
- **Missing README**: No README.md file
- **Short README**: Less than 300 characters
- **Missing sections**: No description, usage, or citation sections
- **Poor tagging**: Missing domain-specific tags

### 3. Scoring System (0-100 scale)
- **Score 0-10**: Critical issues (missing/minimal README, major errors)
- **Score 10-30**: Needs significant improvement (short README, missing sections)
- **Score 30-50**: Moderate quality, could be enhanced
- **Score 50-70**: Good documentation with minor improvements needed
- **Score 70-100**: Excellent card meeting all best practices

## 🚀 Usage Examples

### Basic Discovery
```bash
# Find datasets needing improvement
python find_datasets.py

# Use CLI with options
python -m src.cli.discover --type dataset --limit 100 --needs-improvement
```

### Analysis and Comparison
```bash
# Compare with baseline examples
python -m src.cli.compare --target arcinstitute/opengenome2 --baseline tahoebio/Tahoe-100M

# Analyze specific repository
python -m src.cli.compare analyze --repo-id arcinstitute/opengenome2
```

### Advanced Discovery
```bash
# Search with specific keywords
python -m src.cli.discover --keywords genomics --keywords proteomics --limit 50

# Export results
python -m src.cli.discover --output results.json --format json
```

## 🔧 Configuration

### Environment Variables
```bash
# Required
export HF_TOKEN="your_huggingface_token_here"

# Optional
export API_DEBUG=true
export LOG_LEVEL=INFO
export CACHE_TTL=3600
```

### Settings
The system automatically loads configuration from:
- Environment variables
- `.env` file
- Default values in `settings.py`

## 📊 Performance Metrics

### Discovery Performance
- **Search Coverage**: 192 keywords × 10 results = 1,920+ potential discoveries
- **Actual Results**: 200+ unique datasets per search
- **Processing Speed**: ~30 seconds for comprehensive search
- **Success Rate**: 99.5% of discovered datasets need improvement
- **Scientific Coverage**: All major scientific domains and subdisciplines

## 🛡️ Safety Features

### Human Review Required
- **No Automatic Pushing**: All changes require human review
- **Respect Maintainers**: Always coordinate with repository maintainers
- **Quality Focus**: Better to improve few repos well than many poorly
- **Factual Accuracy**: AI suggestions need human verification

## 📚 Resources

- [Hugging Face Dataset Card Guide](https://huggingface.co/docs/datasets/en/dataset_card)
- [Hugging Face Model Card Guide](https://huggingface.co/docs/hub/model-cards)
- [Example: Poor Card (Arc Institute)](https://huggingface.co/datasets/arcinstitute/opengenome2)
- [Example: Good Card (Tahoe-100M)](https://huggingface.co/datasets/tahoebio/Tahoe-100M)

## Important Notes

- **Respect maintainers**: Always coordinate with repository maintainers
- **Quality over quantity**: Focus on meaningful improvements
- **Community guidelines**: Follow Hugging Face community standards
- **Attribution**: Properly credit original authors and sources

## 🏗️ Architecture

```
src/science_card_improvement/
├── cli/                      # Command-line interfaces
│   ├── discover.py           # Discovery CLI
│   └── compare.py            # Analysis CLI
├── config/                   # Configuration management
│   └── settings.py           # Environment variables
├── discovery/                # Repository discovery
│   └── repository.py         # Discovery logic
├── analysis/                 # Quality analysis
│   └── baseline.py           # Baseline comparison
├── resources/                # Static resources
│   └── science_keywords.json # Science keywords
└── utils/                    # Utilities
    ├── cache.py              # Caching
    └── logger.py             # Logging
```

## License

MIT License - See [LICENSE](LICENSE) for details

---

**Making scientific data more accessible through better documentation**

*All improvements require human review - No automatic pushing*