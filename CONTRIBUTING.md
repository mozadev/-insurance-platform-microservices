# Contributing to Insurance Microservices Platform

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- AWS CLI v2
- Terraform 1.5+
- Git
- Make

### Initial Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/insurance-microservices.git
   cd insurance-microservices
   ```

2. **Install Dependencies**
   ```bash
   # Install Python dependencies for each service
   cd services/policy-svc
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Setup Local Environment**
   ```bash
   # Copy environment template
   cp env.example .env
   
   # Start local infrastructure
   make local-up
   ```

4. **Run Tests**
   ```bash
   make test
   ```

For detailed setup instructions, see [DEVELOPMENT.md](DEVELOPMENT.md).

## Development Workflow

### 1. Create a Feature Branch

Always create a new branch for your work:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Adding or updating tests
- `chore/` - Maintenance tasks

### 2. Make Your Changes

- Write clear, self-documenting code
- Follow the coding standards (see below)
- Add tests for new functionality
- Update documentation as needed
- Keep commits atomic and focused

### 3. Commit Your Changes

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat(policy-svc): add policy validation endpoint"
git commit -m "fix(claim-svc): resolve null pointer in claim processor"
git commit -m "docs: update API documentation for search endpoint"
```

**Commit message format:**
```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code style/formatting
- `refactor` - Code refactoring
- `test` - Tests
- `chore` - Maintenance
- `perf` - Performance improvements
- `ci` - CI/CD changes

### 4. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line Length**: 100 characters (not 79)
- **Quotes**: Double quotes for strings
- **Type Hints**: Required for all function signatures
- **Docstrings**: Google style for all public functions/classes

**Tools we use:**
- `ruff` - Fast Python linter and formatter
- `mypy` - Static type checker
- `black` - Code formatter (compatible with ruff)

**Example:**

```python
from typing import Optional

def process_policy(
    policy_id: str,
    premium: float,
    *,
    coverage_type: Optional[str] = None
) -> dict[str, any]:
    """Process a policy and return the result.
    
    Args:
        policy_id: Unique identifier for the policy
        premium: Annual premium amount in USD
        coverage_type: Type of insurance coverage (optional)
        
    Returns:
        Dictionary containing processing results
        
    Raises:
        ValueError: If premium is negative
    """
    if premium < 0:
        raise ValueError("Premium cannot be negative")
    
    return {
        "policy_id": policy_id,
        "status": "processed",
        "premium": premium,
    }
```

### Project Structure

Each microservice follows this structure:

```
service-name/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models/              # Pydantic models
│   ├── routers/             # API endpoints
│   ├── repositories/        # Data access layer
│   ├── auth/               # Authentication logic
│   └── events/             # Event publishers/consumers
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   └── test_endpoints.py
├── Dockerfile
├── pyproject.toml          # Project metadata
├── ruff.toml              # Linter config
└── mypy.ini               # Type checker config
```

### Code Quality Checks

Before submitting a PR, run:

```bash
# Format code
make format

# Run linter
make lint

# Run type checker
make typecheck

# Run all checks
make check

# Run tests
make test
```

## Pull Request Process

### Before Submitting

1. ✅ All tests pass
2. ✅ Code is formatted and linted
3. ✅ Type checks pass
4. ✅ Documentation is updated
5. ✅ Commits follow conventional commits
6. ✅ Branch is up to date with main

### PR Template

When creating a PR, please fill out the template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?
Describe testing performed

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code where needed
- [ ] I have updated documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests
- [ ] All tests pass locally
```

### Review Process

1. **Automated Checks**: CI/CD runs automatically
2. **Code Review**: At least 1 approval required
3. **Testing**: QA may test in staging environment
4. **Merge**: Squash and merge to main

**Review timeline:**
- Small PRs (< 100 lines): 1-2 days
- Medium PRs (100-500 lines): 2-4 days
- Large PRs (> 500 lines): 1 week

## Testing Guidelines

### Test Structure

```python
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

class TestPolicyEndpoints:
    """Tests for policy management endpoints."""
    
    def test_create_policy_success(self):
        """Test successful policy creation."""
        payload = {
            "customerId": "CUST-12345678",
            "premium": 1500.00,
            "coverageType": "auto",
        }
        
        response = client.post("/api/v1/policies", json=payload)
        
        assert response.status_code == 201
        assert response.json()["premium"] == 1500.00
    
    def test_create_policy_invalid_premium(self):
        """Test policy creation with invalid premium."""
        payload = {
            "customerId": "CUST-12345678",
            "premium": -100.00,
            "coverageType": "auto",
        }
        
        response = client.post("/api/v1/policies", json=payload)
        
        assert response.status_code == 422
```

### Test Coverage

- **Minimum coverage**: 80%
- **Critical paths**: 100% coverage required
- **Integration tests**: Required for all API endpoints
- **Unit tests**: Required for business logic

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_policies.py

# Run with verbose output
pytest -v
```

## Documentation

### Code Documentation

- **All public APIs**: Full docstrings required
- **Complex logic**: Inline comments explaining "why"
- **Type hints**: Required for all functions
- **Examples**: Include usage examples in docstrings

### API Documentation

- FastAPI generates automatic OpenAPI docs
- Access at: `http://localhost:8000/docs`
- Keep endpoint descriptions up to date

### Architecture Documentation

- Update ADRs for significant decisions
- Location: `docs/ADR-XXX-*.md`
- Follow template in `docs/adr-template.md`

## Questions?

- 💬 **Discussions**: Use GitHub Discussions for questions
- 🐛 **Bugs**: Create an issue with bug template
- 💡 **Feature Requests**: Create an issue with feature template
- 📧 **Email**: [maintainer-email@example.com]

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE)).

---

Thank you for contributing! 🎉

