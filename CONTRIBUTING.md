# Contributing to MemCore

Thank you for your interest in contributing to MemCore! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to help us maintain a healthy and welcoming community.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Set up the development environment**:
   - For Python: `pip install -e ".[dev]"`
4. **Create a branch** for your changes

## Development Environment

### Python Requirements
- Python 3.7+
- Poetry (recommended for dependency management)
- pytest for testing

## Development Workflow

1. **Create an issue** describing the feature or bug
2. **Discuss the implementation** approach in the issue
3. **Implement your changes** with tests
4. **Run the test suite** to ensure everything works
5. **Submit a pull request** referencing the issue

## Coding Standards

### Python
- Follow PEP 8 style guide
- Use type hints
- Write docstrings for all public functions and classes
- Maintain test coverage above 80%

## Testing

### Python
\`\`\`bash
pytest tests/
\`\`\`

## Documentation

- Update documentation for any changed functionality
- Add examples for new features
- Keep the README up to date

## Pull Request Process

1. Ensure your code passes all tests
2. Update documentation as needed
3. Add your changes to the CHANGELOG.md under "Unreleased"
4. Submit your pull request with a clear description of the changes
5. Wait for review and address any feedback

## Feature Requests

Feature requests are welcome! Please create an issue describing the feature and its use cases. Be as specific as possible about what problem the feature would solve.

## Bug Reports

When reporting bugs, please include:
- A clear description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)
- If possible, a minimal code example that reproduces the issue

## Current Priorities

We're currently focusing on:
1. Advanced compression implementation
2. Synchronization system
3. Performance optimizations for large datasets
4. Improved documentation and examples

Contributions in these areas are especially welcome!

## Communication

- **Issues**: Use GitHub issues for bug reports and feature requests
- **Discussions**: Use GitHub discussions for general questions and ideas
- **Discord**: Join our Discord server for real-time communication

Thank you for contributing to MemCore!
