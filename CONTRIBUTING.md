# Contributing to HDX MCP Server

Thank you for your interest in contributing to the HDX MCP Server! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Making Changes](#making-changes)
- [Commit Guidelines](#commit-guidelines)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Code Style](#code-style)

## 🤝 Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please treat all community members with respect and create a welcoming environment for everyone.

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Git
- A GitHub account
- HDX API key (for testing)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/hdx-mcp.git
   cd hdx-mcp
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/dividor/hdx-mcp.git
   ```

## 💻 Development Setup

1. **Install dependencies:**
   ```bash
   uv sync --all-extras --dev
   ```

2. **Set up environment:**
   ```bash
   cp env.example .env
   # Edit .env with your HDX API key and settings
   ```

3. **Verify installation:**
   ```bash
   uv run pytest
   ```

## 🔧 Pre-commit Hooks

We use pre-commit hooks to ensure code quality and consistency. **This is required for all contributors.**

### Install Pre-commit

```bash
# Install the git hook scripts
uv run pre-commit install
```

### What Pre-commit Does

Our pre-commit configuration (`.pre-commit-config.yaml`) automatically:

- **Code Formatting**: Runs `black` to format Python code
- **Import Sorting**: Runs `isort` to organize imports
- **Linting**: Runs `flake8` for code quality checks
- **Type Checking**: Runs `mypy` for static type analysis
- **Security Scanning**: Runs `bandit` for security issues
- **File Checks**: Removes trailing whitespace, fixes end-of-file formatting
- **YAML/JSON Validation**: Checks syntax of configuration files
- **Merge Conflict Detection**: Prevents committing unresolved conflicts
- **Large File Prevention**: Blocks accidentally committed large files
- **Testing**: Runs pytest to ensure tests pass

### Running Pre-commit Manually

```bash
# Run on all files
uv run pre-commit run --all-files

# Run on staged files only
uv run pre-commit run

# Skip pre-commit for emergency commits (not recommended)
git commit --no-verify -m "emergency fix"
```

## 🛠️ Making Changes

### Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes:**
   - Write code following our [Code Style](#code-style)
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes:**
   ```bash
   # Run tests
   uv run pytest

   # Run with coverage
   uv run pytest --cov=src --cov-report=html --cov-report=term-missing

   # Run pre-commit checks
   uv run pre-commit run --all-files
   ```

4. **Commit your changes** (see [Commit Guidelines](#commit-guidelines))

5. **Push and create PR:**
   ```bash
   git push origin feat/your-feature-name
   ```

### Types of Contributions

- **Bug Fixes**: Fix existing issues
- **Features**: Add new functionality
- **Documentation**: Improve docs, examples, or comments
- **Tests**: Add or improve test coverage
- **Performance**: Optimize existing code
- **Refactoring**: Improve code structure without changing functionality

## 📝 Commit Guidelines

We use [Conventional Commits](https://www.conventionalcommits.org/) format:

### Commit Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Commit Types

- **feat:** New features
- **fix:** Bug fixes
- **docs:** Documentation changes
- **style:** Code style changes (formatting, etc.)
- **refactor:** Code refactoring
- **test:** Adding or modifying tests
- **chore:** Build process or auxiliary tool changes
- **perf:** Performance improvements
- **ci:** CI/CD pipeline changes
- **build:** Build system or dependencies

### Examples

```bash
feat: add new HDX data availability tool
fix: resolve OpenAPI schema parsing error
docs: update README with tool examples
test: add unit tests for hdx_search_locations tool
chore: update dependencies to latest versions
```

### Commit Best Practices

- Keep commits atomic (one logical change per commit)
- Write clear, descriptive commit messages
- Reference issues when applicable: `fixes #123`
- Use imperative mood: "add feature" not "added feature"

## 🧪 Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src --cov-report=html --cov-report=term-missing

# Run specific test categories
uv run pytest tests/unit/          # Unit tests
uv run pytest tests/integration/   # Integration tests
uv run pytest tests/security/      # Security tests

# Run specific test file
uv run pytest tests/unit/test_server_functions.py

# Run with verbose output
uv run pytest -v
```

### Test Categories

- **Unit Tests** (`tests/unit/`): Test individual components in isolation
- **Integration Tests** (`tests/integration/`): Test interactions with external APIs
- **Security Tests** (`tests/security/`): Test security features and protections

### Writing Tests

- Place tests in the appropriate `tests/` subdirectory
- Use descriptive test names: `test_hdx_search_locations_with_valid_filters`
- Mock external API calls
- Test both success and error scenarios
- Aim for high test coverage (>90%)

### Manual Testing

Test the server manually with curl (HTTP transport):

```bash
# Start server
uv run hdx-mcp-server --transport http

# Test server info tool
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "hdx_server_info", "arguments": {}}}'
```

## 🔍 Pull Request Process

### Before Submitting

1. **Update your branch:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks:**
   ```bash
   uv run pytest
   uv run pre-commit run --all-files
   ```

3. **Update documentation** if needed

### PR Guidelines

- **Title**: Use conventional commit format
- **Description**: Clearly explain what and why
- **Link Issues**: Reference related issues
- **Screenshots**: Include for UI changes
- **Breaking Changes**: Clearly document any breaking changes

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Other: ___

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and linting
2. **Peer Review**: At least one maintainer reviews the code
3. **Feedback**: Address any requested changes
4. **Approval**: Maintainer approves and merges

## 🐛 Issue Guidelines

### Before Creating an Issue

1. **Search existing issues** to avoid duplicates
2. **Check documentation** for common solutions
3. **Test with latest version**

### Bug Reports

Include:
- **Environment**: OS, Python version, package version
- **Steps to reproduce** the issue
- **Expected behavior**
- **Actual behavior**
- **Error messages** (full stack trace)
- **Minimal code example**
- **HDX API key status** (valid/invalid, without exposing the key)

### Feature Requests

Include:
- **Clear description** of the feature
- **Use case** and motivation
- **Proposed solution** (if you have one)
- **Alternatives considered**

## 🎨 Code Style

### Python Style Guide

- **Formatter**: Black (line length: 88 characters)
- **Import Sorting**: isort (Black-compatible profile)
- **Linting**: flake8 with extensions for complexity and security
- **Type Checking**: mypy (strict mode)
- **Type Hints**: Use type hints for function signatures
- **Docstrings**: Google style docstrings

### Code Quality Requirements

1. **Type Hints**: All functions must have type hints
2. **Docstrings**: All public functions and classes must have docstrings
3. **Test Coverage**: Minimum 90% test coverage for new code
4. **Security**: No security vulnerabilities (checked by Bandit)
5. **Complexity**: Keep cyclomatic complexity under 10

### Code Quality Commands

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
uv run pre-commit run --all-files
```

## 🚀 Adding Custom Tools

### Process

1. Add your tool function in the `_register_custom_tools` method in `src/hdx_mcp_server/server.py`
2. Include proper type hints and documentation
3. Add corresponding tests in `tests/unit/test_custom_tools.py`
4. Update the README with documentation for your tool

### New HDX API Endpoints

New HDX API endpoints are automatically included when the OpenAPI specification is updated. No code changes are required.

## 🔄 Release Process

For maintainers:

1. **Version Bump**: Update version in `pyproject.toml`
2. **Changelog**: Update release notes
3. **Tag Release**: Create git tag
4. **GitHub Release**: Create release with notes
5. **PyPI**: Automated via GitHub Actions

## 📞 Getting Help

- **Documentation**: Check the README and code comments
- **Issues**: Create a [GitHub issue](https://github.com/dividor/hdx-mcp/issues) for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **HDX API**: Consult [HDX HAPI documentation](https://hdx-hapi.readthedocs.io/)

## 🙏 Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- Project acknowledgments

Thank you for contributing to the HDX MCP Server! 🎉
