# ═══════════════════════════════════════════════════════════════════════════════
# Backlink Broadcast - Development Makefile
# ═══════════════════════════════════════════════════════════════════════════════
# Usage: make <target>
# Run 'make help' to see all available targets
# ═══════════════════════════════════════════════════════════════════════════════

.PHONY: help install install-dev test lint format type-check clean run \
        build pre-commit setup-hooks coverage docs

.DEFAULT_GOAL := help

# Colors for terminal output
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m  # No Color

# ─────────────────────────────────────────────────────────────────────────────────
# Help
# ─────────────────────────────────────────────────────────────────────────────────
help:
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)         Backlink Broadcast - Development Commands$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)Setup:$(NC)"
	@echo "  make install        Install production dependencies"
	@echo "  make install-dev    Install all dependencies (including dev tools)"
	@echo "  make setup-hooks    Install pre-commit hooks"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make run            Start the hive (queen orchestrator)"
	@echo "  make run-once       Run a single orchestrator cycle"
	@echo "  make status         Check hive status"
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@echo "  make test           Run all tests"
	@echo "  make test-fast      Run tests without coverage"
	@echo "  make test-unit      Run unit tests only"
	@echo "  make coverage       Run tests with coverage report"
	@echo ""
	@echo "$(GREEN)Code Quality:$(NC)"
	@echo "  make lint           Run linter (ruff)"
	@echo "  make format         Format code (ruff + isort)"
	@echo "  make type-check     Run type checker (mypy)"
	@echo "  make check          Run all checks (lint + type-check)"
	@echo "  make pre-commit     Run all pre-commit hooks"
	@echo ""
	@echo "$(GREEN)Build:$(NC)"
	@echo "  make build          Build package"
	@echo "  make clean          Clean build artifacts"
	@echo ""

# ─────────────────────────────────────────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────────────────────────────────────────
install:
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	pip install -e .

install-dev:
	@echo "$(BLUE)Installing all dependencies (including dev tools)...$(NC)"
	pip install -e ".[dev,twitter,browser]"

setup-hooks:
	@echo "$(BLUE)Setting up pre-commit hooks...$(NC)"
	pip install pre-commit
	pre-commit install
	@echo "$(GREEN)Pre-commit hooks installed!$(NC)"

# ─────────────────────────────────────────────────────────────────────────────────
# Running the Hive
# ─────────────────────────────────────────────────────────────────────────────────
run:
	@echo "$(BLUE)Starting the hive...$(NC)"
	python -m hive.queen.orchestrator run

run-once:
	@echo "$(BLUE)Running single orchestrator cycle...$(NC)"
	python -m hive.queen.orchestrator once

status:
	@echo "$(BLUE)Checking hive status...$(NC)"
	python -m hive.queen.orchestrator status

# ─────────────────────────────────────────────────────────────────────────────────
# Testing
# ─────────────────────────────────────────────────────────────────────────────────
test:
	@echo "$(BLUE)Running all tests with coverage...$(NC)"
	pytest --cov=hive --cov-report=term-missing --cov-report=html

test-fast:
	@echo "$(BLUE)Running tests (no coverage)...$(NC)"
	pytest

test-unit:
	@echo "$(BLUE)Running unit tests only...$(NC)"
	pytest -m unit

coverage:
	@echo "$(BLUE)Generating coverage report...$(NC)"
	pytest --cov=hive --cov-report=html
	@echo "$(GREEN)Coverage report generated in htmlcov/index.html$(NC)"

# ─────────────────────────────────────────────────────────────────────────────────
# Code Quality
# ─────────────────────────────────────────────────────────────────────────────────
lint:
	@echo "$(BLUE)Running linter...$(NC)"
	ruff check hive tests

format:
	@echo "$(BLUE)Formatting code...$(NC)"
	ruff format hive tests
	ruff check --fix hive tests

type-check:
	@echo "$(BLUE)Running type checker...$(NC)"
	mypy hive --ignore-missing-imports

check: lint type-check
	@echo "$(GREEN)All checks passed!$(NC)"

pre-commit:
	@echo "$(BLUE)Running pre-commit hooks on all files...$(NC)"
	pre-commit run --all-files

# ─────────────────────────────────────────────────────────────────────────────────
# Build
# ─────────────────────────────────────────────────────────────────────────────────
build:
	@echo "$(BLUE)Building package...$(NC)"
	pip install build
	python -m build
	@echo "$(GREEN)Package built in dist/$(NC)"

clean:
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(NC)"

# ─────────────────────────────────────────────────────────────────────────────────
# Cache Management
# ─────────────────────────────────────────────────────────────────────────────────
cache-reset:
	@echo "$(BLUE)Resetting persistent cache...$(NC)"
	python -m hive.utils.cache_manager reset

cache-refresh:
	@echo "$(BLUE)Refreshing persistent cache...$(NC)"
	python -m hive.utils.cache_manager refresh
