# Contributing to HDX MCP Server

Thank you for your interest in contributing to the HDX MCP Server! This document provides guidelines and instructions for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- [UV](https://docs.astral.sh/uv/) package manager (recommended)
- Git
- HDX API key for testing (optional, but recommended)

### Initial Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/hdx-mcp-server.git
   cd hdx-mcp-server
   ```

2. **Install UV (if not already installed):**
   ```bash
   # macOS and Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. **Set up the development environment:**
   ```bash
   # Install all dependencies including dev dependencies
   uv sync --all-extras --dev
   
   # Set up environment configuration
   cp env.example .env
   # Edit .env with your HDX API key and settings
   ```

4. **Install pre-commit hooks:**
   ```bash
   uv run pre-commit install
   ```

## Development Workflow

### Project Structure

```
hdx-mcp-server/
├── src/hdx_mcp_server/     # Main source code
│   ├── __init__.py         # Package initialization
│   ├── __main__.py         # CLI entry point
│   └── server.py           # Main server implementation
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── security/          # Security tests
│   └── conftest.py        # Shared test fixtures
├── .github/workflows/     # GitHub Actions CI/CD
├── .pre-commit-config.yaml # Pre-commit hooks configuration
└── pyproject.toml         # Project configuration
```

### Running Commands

All development commands use UV for consistency and performance:

#### Testing

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest tests/unit/           # Unit tests only
uv run pytest tests/integration/    # Integration tests only
uv run pytest tests/security/       # Security tests only

# Run tests with coverage
uv run pytest --cov=src --cov-report=html --cov-report=term-missing

# Run tests for a specific file
uv run pytest tests/unit/test_server_initialization.py -v
```

#### Code Quality

```bash
# Format code
uv run black src/ tests/
uv run isort src/ tests/

# Check code quality
uv run flake8 src/ tests/
uv run mypy src/

# Security scanning
uv run bandit -r src/

# Run all quality checks
uv run black --check src/ tests/
uv run isort --check-only src/ tests/
uv run flake8 src/ tests/
uv run mypy src/
uv run bandit -r src/
```

#### Running the Server

```bash
# Run with stdio transport (for local MCP clients)
uv run python -m hdx_mcp_server

# Run with HTTP transport (for remote access)
uv run python -m hdx_mcp_server --transport http

# Run with verbose logging
uv run python -m hdx_mcp_server --verbose

# Get help
uv run python -m hdx_mcp_server --help
```

### Code Standards

#### Code Style

- **Black**: Code formatting (line length: 88 characters)
- **isort**: Import sorting (Black-compatible profile)
- **flake8**: Linting with extensions for complexity and security
- **mypy**: Type checking (strict mode)

#### Code Quality Requirements

1. **Type Hints**: All functions must have type hints
2. **Docstrings**: All public functions and classes must have docstrings
3. **Test Coverage**: Minimum 90% test coverage for new code
4. **Security**: No security vulnerabilities (checked by Bandit)
5. **Complexity**: Keep cyclomatic complexity under 10

#### Example Code Style

```python
"""Module docstring describing the purpose."""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ExampleClass:
    """Class docstring describing the class purpose."""
    
    def __init__(self, api_key: str, timeout: float = 30.0) -> None:
        """Initialize the class with required parameters.
        
        Args:
            api_key: The API key for authentication
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
    
    async def fetch_data(self, endpoint: str) -> Dict[str, Any]:
        """Fetch data from the specified endpoint.
        
        Args:
            endpoint: The API endpoint to fetch from
            
        Returns:
            Dictionary containing the API response
            
        Raises:
            ValueError: If endpoint is invalid
            httpx.RequestError: If the request fails
        """
        if not endpoint:
            raise ValueError("Endpoint cannot be empty")
        
        # Implementation here
        return {"data": "example"}
```

### Testing Guidelines

#### Test Organization

Tests are organized by category:

- **Unit Tests** (`tests/unit/`): Test individual components in isolation
- **Integration Tests** (`tests/integration/`): Test interactions with external APIs
- **Security Tests** (`tests/security/`): Test security features and vulnerability protection

#### Writing Tests

1. **Use descriptive test names**: `test_server_initialization_with_valid_environment`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Use fixtures**: Leverage shared fixtures from `conftest.py`
4. **Mock external calls**: Use `unittest.mock` for HTTP requests and external dependencies
5. **Test edge cases**: Include error conditions and boundary values

#### Example Test

```python
import pytest
from unittest.mock import patch, MagicMock
from src.hdx_mcp_server import HDXMCPServer


class TestServerInitialization:
    """Test server initialization and configuration."""
    
    def test_server_initialization_with_valid_environment(self, mock_env_vars, sample_openapi_spec):
        """Test that server initializes correctly with valid environment variables."""
        # Arrange
        with patch('httpx.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = sample_openapi_spec
            mock_get.return_value = mock_response
            
            with patch('fastmcp.FastMCP.from_openapi') as mock_fastmcp:
                mock_fastmcp.return_value = MagicMock()
                
                # Act
                server = HDXMCPServer()
                
                # Assert
                assert server.api_key == "test_api_key_12345"
                assert server.base_url == "https://test.hapi.humdata.org/api/v2"
```

### Pre-commit Hooks

Pre-commit hooks automatically run quality checks before each commit:

```bash
# Install hooks (one-time setup)
uv run pre-commit install

# Run hooks manually
uv run pre-commit run --all-files

# Update hook versions
uv run pre-commit autoupdate
```

The hooks include:
- Code formatting (Black, isort)
- Linting (flake8, pylint)
- Type checking (mypy)
- Security scanning (Bandit)
- Basic file checks (trailing whitespace, YAML syntax, etc.)
- Quick test run (unit and security tests)

### Continuous Integration

GitHub Actions automatically run on pull requests and pushes:

1. **Tests**: Run on Python 3.8-3.12
2. **Code Quality**: Format checking, linting, type checking
3. **Security**: Security-focused tests and vulnerability scanning
4. **Integration**: Full API integration tests (main branch only)

### Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Follow the code standards above
   - Add tests for new functionality
   - Update documentation if needed

3. **Test your changes:**
   ```bash
   # Run all quality checks
   uv run pre-commit run --all-files
   
   # Run full test suite
   uv run pytest --cov=src
   ```

4. **Commit and push:**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   git push origin feature/your-feature-name
   ```

5. **Create a pull request:**
   - Use a descriptive title
   - Include a detailed description of changes
   - Reference any related issues
   - Add the `run-integration-tests` label if integration tests are needed

### Commit Message Format

Follow conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(server): add support for custom timeout configuration
fix(auth): handle empty API key environment variable
docs(readme): update installation instructions for UV
test(security): add tests for environment variable injection
```

### Environment Variables

For development and testing, configure these environment variables in `.env`:

```bash
# Required
HDX_API_KEY=your_hdx_api_key_here

# Optional (with defaults)
HDX_BASE_URL=https://hapi.humdata.org/api/v2
HDX_OPENAPI_URL=https://hapi.humdata.org/openapi.json
HDX_TIMEOUT=30.0
HDX_APP_NAME=hdx-mcp-server
HDX_APP_EMAIL=your.email@example.com
MCP_HOST=localhost
MCP_PORT=8000
```

### Security Considerations

1. **Never commit sensitive data**: API keys, passwords, etc.
2. **Use environment variables**: For all configuration
3. **Validate inputs**: Especially user-provided data
4. **Follow security best practices**: Use HTTPS, validate certificates, etc.
5. **Run security tests**: Include security tests in your test suite

### Getting Help

- **Issues**: Create a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Discord/Slack**: [Link to community chat if available]

### License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

## Release Process

Releases are automated through GitHub Actions when a version tag is pushed:

```bash
# Create and push a version tag
git tag v1.1.0
git push origin v1.1.0
```

This will:
1. Run the full test suite
2. Build the package
3. Create a GitHub release
4. Upload release artifacts

---

Thank you for contributing to HDX MCP Server! 🚀
