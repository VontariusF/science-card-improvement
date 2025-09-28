#!/bin/bash
# Minimal installation script for Science Card Improvement Toolkit

echo "🔬 Science Card Improvement Toolkit - Minimal Installation"
echo "=========================================================="

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check Python version
python_version=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $python_version detected. Python 3.8+ is required."
    exit 1
fi

echo "✅ Python $python_version detected"

# Install package in development mode
echo "📦 Installing package..."
pip install -e .

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your HF_TOKEN"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your Hugging Face token"
echo "2. Run: python find_datasets.py"
echo "3. Or use CLI: python -m src.cli.discover --help"
echo ""
echo "Essential files:"
echo "- find_datasets.py (main discovery script)"
echo "- src/cli/discover.py (CLI interface)"
echo "- src/cli/compare.py (analysis CLI)"
echo "- src/science_card_improvement/resources/science_keywords.json (192 keywords)"
