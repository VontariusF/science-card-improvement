.PHONY: help install install-dev test test-unit test-integration test-e2e lint format type-check clean build docs serve-docs docker-build docker-run setup-pre-commit

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
PROJECT_NAME := science-card-improvement
DOCKER_IMAGE := $(PROJECT_NAME):latest
COVERAGE_THRESHOLD := 80

# Colors for terminal output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install production dependencies
	@echo "$(GREEN)Installing production dependencies...$(NC)"
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e .
	@echo "$(GREEN)Installation complete!$(NC)"

install-dev: ## Install development dependencies
	@echo "$(GREEN)Installing development dependencies...$(NC)"
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e ".[dev,test,docs]"
	pre-commit install
	@echo "$(GREEN)Development installation complete!$(NC)"

test: ## Run all tests with coverage
	@echo "$(GREEN)Running all tests...$(NC)"
	pytest -v --cov=science_card_improvement --cov-report=term-missing --cov-report=html --cov-fail-under=$(COVERAGE_THRESHOLD)

test-unit: ## Run unit tests only
	@echo "$(GREEN)Running unit tests...$(NC)"
	pytest tests/unit -v -m unit

test-integration: ## Run integration tests only
	@echo "$(GREEN)Running integration tests...$(NC)"
	pytest tests/integration -v -m integration

test-e2e: ## Run end-to-end tests only
	@echo "$(GREEN)Running end-to-end tests...$(NC)"
	pytest tests/e2e -v -m e2e

test-watch: ## Run tests in watch mode
	@echo "$(GREEN)Running tests in watch mode...$(NC)"
	pytest-watch --clear --nobeep

lint: ## Run linting checks
	@echo "$(GREEN)Running linters...$(NC)"
	ruff check src tests scripts
	flake8 src tests scripts --max-line-length=100 --extend-ignore=E203,W503
	@echo "$(GREEN)Linting complete!$(NC)"

format: ## Format code with black and isort
	@echo "$(GREEN)Formatting code...$(NC)"
	black src tests scripts
	isort src tests scripts
	ruff check --fix src tests scripts
	@echo "$(GREEN)Formatting complete!$(NC)"

type-check: ## Run type checking with mypy
	@echo "$(GREEN)Running type checks...$(NC)"
	mypy src --ignore-missing-imports
	@echo "$(GREEN)Type checking complete!$(NC)"

security-check: ## Run security vulnerability scan
	@echo "$(GREEN)Running security checks...$(NC)"
	pip-audit
	bandit -r src -f json -o security-report.json
	@echo "$(GREEN)Security check complete!$(NC)"

clean: ## Clean build artifacts and cache files
	@echo "$(GREEN)Cleaning build artifacts...$(NC)"
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .ruff_cache .mypy_cache
	rm -rf htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)Cleanup complete!$(NC)"

build: clean ## Build distribution packages
	@echo "$(GREEN)Building distribution packages...$(NC)"
	$(PYTHON) -m build
	@echo "$(GREEN)Build complete!$(NC)"

docs: ## Build documentation
	@echo "$(GREEN)Building documentation...$(NC)"
	cd docs && $(MAKE) clean html
	@echo "$(GREEN)Documentation built! Open docs/_build/html/index.html$(NC)"

serve-docs: docs ## Build and serve documentation locally
	@echo "$(GREEN)Serving documentation at http://localhost:8000$(NC)"
	$(PYTHON) -m http.server 8000 --directory docs/_build/html

docker-build: ## Build Docker image
	@echo "$(GREEN)Building Docker image...$(NC)"
	docker build -t $(DOCKER_IMAGE) .
	@echo "$(GREEN)Docker image built: $(DOCKER_IMAGE)$(NC)"

docker-run: ## Run Docker container
	@echo "$(GREEN)Running Docker container...$(NC)"
	docker run -it --rm \
		-v $(PWD):/app \
		-e HF_TOKEN=$${HF_TOKEN} \
		$(DOCKER_IMAGE)

setup-pre-commit: ## Setup pre-commit hooks
	@echo "$(GREEN)Setting up pre-commit hooks...$(NC)"
	pre-commit install
	pre-commit install --hook-type commit-msg
	pre-commit run --all-files
	@echo "$(GREEN)Pre-commit setup complete!$(NC)"

validate: lint type-check test security-check ## Run all validation checks
	@echo "$(GREEN)All validation checks passed!$(NC)"

ci: validate ## Run CI pipeline locally
	@echo "$(GREEN)CI pipeline complete!$(NC)"

release: validate build ## Prepare for release
	@echo "$(GREEN)Release preparation complete!$(NC)"
	@echo "$(YELLOW)Don't forget to:$(NC)"
	@echo "  1. Update version in pyproject.toml"
	@echo "  2. Update CHANGELOG.md"
	@echo "  3. Create git tag"
	@echo "  4. Push to PyPI"

dev: install-dev ## Setup development environment
	@echo "$(GREEN)Development environment ready!$(NC)"
	@echo "$(YELLOW)Run 'make help' to see available commands$(NC)"

quick-start: install ## Quick start for new users
	@echo "$(GREEN)Quick start complete!$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Set your HF token: export HF_TOKEN='your_token_here'"
	@echo "  2. Run discovery: sci-discover --type dataset --limit 10"
	@echo "  3. Assess quality: sci-assess --repo-id <repo-id>"
	@echo "  4. Generate card: sci-generate --repo-id <repo-id>"
	@echo ""
	@echo "$(GREEN)Happy contributing!$(NC)"