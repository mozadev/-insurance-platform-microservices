.PHONY: help setup compose:up compose:down bootstrap demo lint type test clean

# Default target
help:
	@echo "Available commands:"
	@echo "  setup          - Install dependencies and setup development environment"
	@echo "  compose:up      - Start local development stack with Docker Compose"
	@echo "  compose:down    - Stop local development stack"
	@echo "  bootstrap       - Create AWS resources in LocalStack"
	@echo "  demo            - Run demo with sample data"
	@echo "  lint            - Run linting with ruff"
	@echo "  type            - Run type checking with mypy"
	@echo "  test            - Run all tests"
	@echo "  clean           - Clean up temporary files and containers"

# Setup development environment
setup:
	@echo "Setting up development environment..."
	python -m pip install --upgrade pip
	pip install uv
	uv sync
	pre-commit install
	@echo "Setup complete!"

# Docker Compose commands
compose:up:
	@echo "Starting local development stack..."
	docker-compose -f local/docker-compose.yml up -d
	@echo "Waiting for services to be ready..."
	sleep 30
	@echo "Services started! Check status with: docker-compose -f local/docker-compose.yml ps"

compose:down:
	@echo "Stopping local development stack..."
	docker-compose -f local/docker-compose.yml down
	@echo "Stack stopped!"

# Bootstrap AWS resources
bootstrap:
	@echo "Bootstrapping AWS resources in LocalStack..."
	chmod +x local/bootstrap/create-resources.sh
	./local/bootstrap/create-resources.sh
	@echo "Bootstrap complete!"

# Run demo
demo:
	@echo "Running demo with sample data..."
	python local/bootstrap/seed-data.py
	@echo "Demo complete! Check the logs for results."

# Quality checks
lint:
	@echo "Running linting..."
	ruff check services/ tests/ local/bootstrap/
	@echo "Linting complete!"

type:
	@echo "Running type checking..."
	mypy services/ tests/ local/bootstrap/
	@echo "Type checking complete!"

test:
	@echo "Running tests..."
	pytest tests/ -v --cov=services --cov-report=html --cov-report=term
	@echo "Tests complete!"

# Clean up
clean:
	@echo "Cleaning up..."
	docker-compose -f local/docker-compose.yml down -v
	docker system prune -f
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	@echo "Cleanup complete!"

# Service-specific commands
test-policy:
	pytest tests/policy-svc/ -v

test-claim:
	pytest tests/claim-svc/ -v

test-search:
	pytest tests/search-svc/ -v

test-ingest:
	pytest tests/ingest-svc/ -v

# Development helpers
logs:
	docker-compose -f local/docker-compose.yml logs -f

restart:
	docker-compose -f local/docker-compose.yml restart

status:
	docker-compose -f local/docker-compose.yml ps
