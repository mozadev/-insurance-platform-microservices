.PHONY: help setup clean test lint format check
.PHONY: local-up local-down local-bootstrap
.PHONY: docker-build tf-plan tf-apply

help:
	@echo "Insurance Microservices - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup          - Setup development environment"
	@echo "  make clean          - Clean temporary files"
	@echo ""
	@echo "Development:"
	@echo "  make local-up       - Start local infrastructure"
	@echo "  make local-down     - Stop local infrastructure"
	@echo "  make local-bootstrap - Create local resources"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests"
	@echo "  make test-coverage  - Run tests with coverage"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           - Run linter"
	@echo "  make format         - Format code"
	@echo "  make typecheck      - Run type checker"
	@echo "  make check          - Run all checks"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   - Build Docker images"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make tf-plan        - Terraform plan"
	@echo "  make tf-apply       - Terraform apply"

setup:
	@echo "Setting up development environment..."
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	@echo "✓ Setup complete! Run 'source venv/bin/activate'"

clean:
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleanup complete!"

local-up:
	@echo "Starting local infrastructure..."
	docker-compose -f local/docker-compose.yml up -d
	@echo "✓ Infrastructure started!"

local-down:
	docker-compose -f local/docker-compose.yml down

local-bootstrap:
	cd local/bootstrap && ./create-resources.sh

test:
	pytest tests/ -v

test-coverage:
	pytest tests/ -v --cov=services --cov=shared --cov-report=html
	@echo "✓ Coverage report: htmlcov/index.html"

lint:
	ruff check services/ shared/ tests/

format:
	ruff format services/ shared/ tests/
	ruff check --fix services/ shared/ tests/ || true

typecheck:
	mypy services/ shared/

check: lint typecheck
	@echo "✓ All checks passed!"

docker-build:
	docker build -t insurance-ingest-svc:latest -f services/ingest-svc/Dockerfile .

tf-plan:
	cd infra/terraform/envs/dev && terraform plan

tf-apply:
	cd infra/terraform/envs/dev && terraform apply
