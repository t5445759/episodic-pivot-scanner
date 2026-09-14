# Contributing to Episodic Pivot Scanner

Thank you for your interest in contributing! This document provides guidelines for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/episodic-pivot-scanner.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Install dev dependencies: `pip install -r requirements.txt`

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install dev tools
pip install black flake8 mypy pytest pytest-asyncio

# Run tests
pytest

# Format code
black src/

# Lint
flake8 src/
```

## Code Style

- Use **Black** for formatting
- Follow **PEP 8** guidelines
- Add type hints to functions
- Write docstrings for all modules and functions
- Keep functions focused and modular

## Commit Messages

- Use clear, descriptive messages
- Start with action word: "Add", "Fix", "Update", "Remove"
- Include context about what changed and why

Example:
```
Add gap filter validation in scanner

- Added min/max gap validation
- Improved error handling for invalid gaps
- Updated tests
```

## Pull Request Process

1. Update README.md with any new features or changes
2. Update CHANGELOG.md
3. Ensure all tests pass: `pytest`
4. Ensure code is formatted: `black src/`
5. Ensure no lint issues: `flake8 src/`
6. Create pull request with detailed description

## Testing

- Write tests for new features
- Run test suite before submitting PR
- Aim for >80% code coverage

```bash
pytest --cov=src/
```

## Areas for Contribution

- Bug fixes
- Documentation improvements
- New data sources
- Additional indicators
- Performance optimizations
- Test coverage
- Examples and tutorials

## Questions?

Open an issue or discussion for questions. We're happy to help!

---

Thank you for contributing to make Episodic Pivot Scanner better! 🚀
