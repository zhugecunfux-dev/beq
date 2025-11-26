# Contributing to BEQ

Thank you for your interest in contributing to BEQ! This document provides guidelines and instructions for contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/beq.git
   cd beq
   ```
3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"  # Install dev dependencies
   ```

2. Set up pre-commit hooks (optional but recommended):
   ```bash
   pip install pre-commit
   pre-commit install
   ```

3. Configure your environment:
   ```bash
   cp .env.example .env
   # Edit .env with your paths
   ```

## Code Style

We follow standard Python conventions:

- **Formatting**: Use `black` for code formatting
- **Import sorting**: Use `isort`
- **Linting**: Use `flake8`
- **Type hints**: Use `mypy` for type checking

Run all checks:
```bash
black .
isort .
flake8 .
mypy .
```

## Testing

Before submitting a pull request, ensure all tests pass:

```bash
pytest tests/
```

If you add new functionality, please add corresponding tests.

## Commit Messages

Write clear, descriptive commit messages:

- Use present tense ("Add feature" not "Added feature")
- Keep first line under 72 characters
- Reference issues and pull requests when relevant

Example:
```
Add support for Gemini LLM models

- Implement GeminiGrader class in equivalence/llm_grader_gemini.py
- Add configuration options for Gemini API
- Update documentation

Fixes #123
```

## Pull Request Process

1. **Update documentation**: If you change APIs or add features, update README.md
2. **Add tests**: Ensure your changes are tested
3. **Update CHANGELOG**: Add your changes to CHANGELOG.md (if it exists)
4. **Submit PR**: Create a pull request with a clear description

### PR Checklist

- [ ] Code follows the project's style guidelines
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Commit messages are clear and descriptive

## Areas for Contribution

### High Priority

1. **Test Suite**: Add comprehensive unit and integration tests
2. **Documentation**: Improve code documentation and examples
3. **LLM Backends**: Add support for additional LLM models (GPT-4, Gemini, Claude)
4. **Retrieval**: Improve retrieval strategies

### Medium Priority

1. **Web Interface**: Build a web UI for equivalence checking
2. **Benchmarks**: Add more benchmark datasets
3. **Performance**: Optimize REPL communication and LLM inference
4. **Error Handling**: Improve error messages and recovery

### Low Priority

1. **IDE Integration**: VSCode/Emacs plugins
2. **Multi-language Support**: Support for Coq, Isabelle, etc.
3. **Visualization**: Proof visualization tools

## Code Organization

```
beq/
├── equivalence/      # Core equivalence checking
├── autoformalizer/   # Auto-formalization
├── retriever/        # Theorem retrieval
├── common/           # Shared utilities
├── data/             # Datasets
├── examples/         # Example scripts
└── tests/            # Test suite
```

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Check existing issues before creating new ones

## Code of Conduct

Be respectful and constructive in all interactions. We aim to create a welcoming environment for all contributors.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
