.PHONY: help setup install test lint format clean run

help:
	@echo "JARVIS MCP - Development Commands"
	@echo ""
	@echo "setup       Install development environment"
	@echo "install     Install package"
	@echo "test        Run tests"
	@echo "test-cov    Run tests with coverage"
	@echo "lint        Check code style"
	@echo "format      Auto-format code"
	@echo "type        Run type checks"
	@echo "clean       Remove build artifacts"
	@echo "run         Run MCP server"

setup:
	python -m venv venv
	source venv/bin/activate || . venv/Scripts/activate
	pip install -e ".[dev]"
	cp .env.example .env
	@echo ""
	@echo "Setup complete! Next steps:"
	@echo "1. Edit .env and add your NVIDIA_API_KEY"
	@echo "2. Run: make test"

install:
	pip install -e .

dev-install:
	pip install -e ".[dev]"

test:
	pytest

test-cov:
	pytest --cov=jarvis_mcp --cov-report=html --cov-report=term

lint:
	flake8 jarvis_mcp tests

format:
	black jarvis_mcp tests

type:
	mypy jarvis_mcp

clean:
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run:
	python -m jarvis_mcp.mcp_server

all: clean format lint test
	@echo "All checks passed!"
