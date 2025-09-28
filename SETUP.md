# Minimal Setup Guide

## Essential Components Only

### 1. Core Files (Required)
```
science-card-improvement/
├── find_datasets.py                    # Main discovery script
├── pyproject.toml                      # Package configuration
├── requirements.txt                    # Essential dependencies
├── .env                                # Your HF token
├── install.sh                          # Installation script
└── src/science_card_improvement/
    ├── cli/
    │   ├── discover.py                 # Discovery CLI
    │   └── compare.py                  # Analysis CLI
    ├── config/
    │   └── settings.py                 # Configuration
    ├── resources/
    │   └── science_keywords.json       # 192 science keywords
    ├── discovery/
    │   └── repository.py               # Discovery logic
    ├── analysis/
    │   └── baseline.py                 # Analysis logic
    └── utils/
        ├── cache.py                    # Caching
        └── logger.py                   # Logging
```

### 2. Quick Installation
```bash
# Run installation script
./install.sh

# Or manual installation
pip install -e .
cp .env.example .env
# Edit .env and add your HF_TOKEN
```

### 3. Essential Commands
```bash
# Discover datasets needing improvement
python find_datasets.py

# Use CLI for more control
python -m src.cli.discover --limit 200 --verbose

# Analyze specific repository
python -m src.cli.compare analyze --repo-id arcinstitute/opengenome2
```

### 4. What You Can Remove
- `tests/` - Entire directory (development only)
- `docs/` - Entire directory (optional documentation)
- `examples/` - Example files (optional)
- `templates/` - Templates (optional for basic usage)
- `Makefile` - Development automation
- `Dockerfile` & `docker-compose.yml` - Containerization
- `.github/workflows/` - CI/CD
- `README_ENHANCED.md` - Redundant documentation
- `BASELINE_COMPARISON.md` - Detailed docs
- `GETTING_STARTED.md` - Redundant

### 5. Environment Variables
```bash
# Required
export HF_TOKEN="your_huggingface_token_here"

# Optional
export API_DEBUG=true
export LOG_LEVEL=INFO
```

## That's It!

The system needs only these essential components to run successfully. Everything else is optional or for development purposes.
