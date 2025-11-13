# Contributing to TempoNest

Thank you for your interest in contributing to TempoNest! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Coding Standards](#coding-standards)
- [Project Structure](#project-structure)

## Code of Conduct

By participating in this project, you agree to maintain a respectful, inclusive, and collaborative environment for all contributors.

## Getting Started

### Prerequisites

- Docker 24+ and Docker Compose V2
- Python 3.11+ (for local development)
- Node.js 18+ (for console app)
- Git
- 8GB+ RAM recommended

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/temponest.git
   cd temponest
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/ORIGINAL-OWNER/temponest.git
   ```

## Development Setup

### Quick Start

Run the automated setup script:

```bash
./infra/scripts/setup.sh
```

### Manual Setup

1. **Start Docker services:**
   ```bash
   cd docker
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```

2. **Configure environment:**
   Copy `docker/.env.example` to `docker/.env` and fill in required values:
   ```bash
   cp docker/.env.example docker/.env
   # Edit docker/.env with your values
   ```

3. **Install Python dependencies** (for local development):
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r services/agents/requirements.txt
   pip install -r requirements-migrations.txt
   ```

4. **Run tests:**
   ```bash
   # Run all tests
   pytest services/agents/tests/
   pytest services/scheduler/tests/

   # Run with coverage
   pytest --cov=app services/agents/tests/
   ```

## Making Changes

### Branch Naming

Use descriptive branch names following this pattern:

- `feat/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `perf/description` - Performance improvements
- `refactor/description` - Code refactoring
- `test/description` - Adding or updating tests

Examples:
```bash
git checkout -b feat/add-oauth-support
git checkout -b fix/database-connection-leak
git checkout -b docs/update-api-examples
```

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```bash
feat(agents): Add support for GPT-4 Turbo model

- Add configuration for GPT-4 Turbo
- Update agent initialization logic
- Add tests for new model

Closes #123
```

```bash
fix(scheduler): Resolve race condition in task queue

The task queue had a race condition when multiple workers
tried to dequeue the same task simultaneously.

- Add proper locking mechanism
- Add integration tests to verify fix
- Update documentation

Fixes #456
```

## Testing

### Running Tests

```bash
# Run all tests with coverage
pytest --cov=app --cov-report=html services/agents/tests/

# Run specific test file
pytest services/agents/tests/unit/test_agent_manager.py

# Run tests matching a pattern
pytest -k "test_agent_creation"

# Run with verbose output
pytest -v services/agents/tests/
```

### Writing Tests

- Place unit tests in `services/<service>/tests/unit/`
- Place integration tests in `services/<service>/tests/integration/`
- Follow the existing test structure
- Aim for >80% code coverage
- Use pytest fixtures for common setup

**Example test:**
```python
import pytest
from app.services.agent_manager import AgentManager

@pytest.fixture
def agent_manager():
    """Create agent manager for testing."""
    return AgentManager()

def test_agent_creation(agent_manager):
    """Test that agents can be created successfully."""
    agent = agent_manager.create_agent("test-agent")
    assert agent.name == "test-agent"
    assert agent.status == "initialized"
```

### Testing Standards

See [TESTING_STANDARDS.md](./TESTING_STANDARDS.md) for comprehensive testing guidelines, including:
- Test coverage requirements
- Mocking strategies
- Integration test patterns
- E2E test approaches

## Submitting Changes

### Pull Request Process

1. **Update your fork:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Ensure all tests pass:**
   ```bash
   pytest services/agents/tests/
   pytest services/scheduler/tests/
   ```

3. **Check code quality:**
   ```bash
   # Run linters (if configured)
   flake8 services/agents/app/
   black --check services/agents/app/
   mypy services/agents/app/
   ```

4. **Push to your fork:**
   ```bash
   git push origin feat/your-feature-name
   ```

5. **Create Pull Request:**
   - Go to the original repository on GitHub
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill in the PR template with:
     - Description of changes
     - Related issue numbers
     - Testing performed
     - Screenshots (if UI changes)

### PR Requirements

- ✅ All tests passing
- ✅ No merge conflicts
- ✅ Code follows project conventions
- ✅ Documentation updated (if needed)
- ✅ Commit messages follow conventional format
- ✅ PR description is clear and complete

## Coding Standards

### Python

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use docstrings for all public functions/classes
- Prefer async/await over callbacks

**Example:**
```python
from typing import Optional, List
from pydantic import BaseModel

async def fetch_agent_status(
    agent_id: str,
    include_metrics: bool = False
) -> Optional[AgentStatus]:
    """Fetch the current status of an agent.

    Args:
        agent_id: Unique identifier for the agent
        include_metrics: Whether to include performance metrics

    Returns:
        AgentStatus object if found, None otherwise

    Raises:
        AgentNotFoundError: If agent_id doesn't exist
    """
    # Implementation here
    pass
```

### TypeScript/JavaScript (Console App)

- Follow project ESLint configuration
- Use TypeScript for type safety
- Prefer functional components with hooks
- Use async/await over promises

### Database Migrations

- Use Alembic for all schema changes (see [alembic/README.md](./alembic/README.md))
- Always write both `upgrade()` and `downgrade()` functions
- Test rollback functionality
- Keep migrations small and focused

### Docker

- Use multi-stage builds to minimize image size
- Pin specific versions for dependencies
- Add health checks to all services
- Use `.dockerignore` to exclude unnecessary files

## Project Structure

```
temponest/
├── services/
│   ├── agents/          # AI agent service (CrewAI)
│   ├── approval/        # Human approval service
│   ├── scheduler/       # Task scheduling service
│   └── temporal_workers/# Temporal workflow workers
├── shared/              # Shared Python modules
│   ├── auth/           # Authentication utilities
│   ├── redis/          # Redis client
│   └── telemetry/      # OpenTelemetry setup
├── apps/
│   └── console/        # Next.js web console
├── docker/             # Docker configuration
│   ├── migrations/     # Database migrations
│   └── docker-compose.yml
├── infra/              # Infrastructure as Code
│   ├── k8s/           # Kubernetes manifests (placeholder)
│   └── scripts/       # Setup and deployment scripts
├── alembic/           # Alembic migration framework
└── docs/              # Documentation

```

### Key Files

- `services/<service>/app/main.py` - Service entrypoint
- `services/<service>/requirements.txt` - Python dependencies
- `services/<service>/Dockerfile` - Container definition
- `shared/` - Shared utilities (auth, logging, etc.)
- `docker/migrations/` - SQL migration files
- `alembic/` - Alembic migration framework

## Performance Considerations

TempoNest has undergone extensive optimization (145+ hours across 7 phases). When contributing:

- **Profile before optimizing**: Use metrics to identify bottlenecks
- **Cache aggressively**: Leverage Redis for frequently accessed data
- **Use async operations**: Prefer async/await for I/O operations
- **Optimize Docker images**: Use multi-stage builds, Alpine base images
- **Monitor resource usage**: Check memory and CPU impact of changes

See [PERFORMANCE.md](./PERFORMANCE.md) for detailed optimization history.

## Documentation

- Update README.md for user-facing changes
- Add docstrings to all public functions
- Update CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/) format
- Add inline comments for complex logic
- Update API documentation if endpoints change

## Getting Help

- Check existing issues and PRs first
- Open an issue for bugs or feature requests
- Use discussions for questions
- Be specific and provide reproduction steps

## Recognition

Contributors will be acknowledged in:
- Project README
- Release notes
- Git commit history

Thank you for contributing to TempoNest! 🚀
