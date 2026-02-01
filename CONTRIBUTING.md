# Contributing to Kimi Secrets Vault

Thank you for your interest in contributing to Kimi Secrets Vault! This document provides guidelines and instructions for contributing to the project.

## Our Philosophy

Kimi Secrets Vault follows these core principles:

1. **Security First**: Never compromise security for convenience
2. **Local-First Architecture**: User data stays on their machine unless explicitly shared
3. **Extensible by Design**: Plugin system as the primary extension mechanism
4. **Developer Experience**: CLI-first with excellent ergonomics and clear error messages
5. **Transparency**: Clear documentation of limitations and security assumptions

## Getting Started

### Prerequisites
- Python 3.9 or higher
- Git
- `age` encryption tool (for development testing)

### Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/your-username/kimi-secrets-vault.git
   cd kimi-secrets-vault
   ```

2. **Set up virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**:
   ```bash
   pip install -e .[dev]
   ```

4. **Run tests to verify setup**:
   ```bash
   python -m pytest tests/ -v
   ```

## Development Workflow

### 1. Branch Naming Convention
- `feature/` - New features or enhancements
- `bugfix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test improvements
- `chore/` - Maintenance tasks

Example: `feature/github-plugin`, `bugfix/cli-error-handling`

### 2. Code Standards

#### Python Code
- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Keep functions focused and small (< 50 lines when possible)

#### Security Requirements
- Never log sensitive data (credentials, keys, tokens)
- Use the vault's encryption methods for any credential storage
- Validate all user input
- Use `subprocess` without `shell=True` to prevent injection
- Follow the principle of least privilege

#### Testing Requirements
- Write tests for all new functionality
- Maintain or improve test coverage
- Mock external dependencies (APIs, system tools)
- Test edge cases and error conditions

### 3. Testing Your Changes

Run the full test suite:
```bash
python -m pytest tests/ --cov=src/kimi_vault --cov-report=term-missing
```

Run specific test files:
```bash
python -m pytest tests/unit/test_vault.py -v
```

Check code formatting:
```bash
black --check src/ tests/
```

Run linting:
```bash
flake8 src/ tests/ --count --max-complexity=10 --statistics
```

Run type checking:
```bash
mypy src/
```

### 4. Git Hooks
The project includes git hooks that automatically run tests:
- `pre-commit`: Runs quick tests on staged Python files
- `pre-push`: Runs full test suite before allowing pushes

These hooks help maintain code quality. You can skip them temporarily with `--no-verify` flag if needed.

## Contributing Areas

### 1. Plugin Development
Plugins are the primary way to extend Kimi Secrets Vault. See [Plugin Development Guide](docs/development/PLUGIN_DEVELOPMENT.md) for detailed guidelines.

#### Plugin Requirements:
- Must inherit from `BasePlugin` class
- Must implement required abstract methods
- Must include comprehensive tests
- Must handle errors gracefully
- Must not store credentials in plain text

#### Plugin Security Review:
All plugins undergo security review before merging:
1. Input validation
2. Error handling
3. Credential storage practices
4. External API usage patterns
5. Memory safety considerations

### 2. Core Improvements
- Bug fixes in vault, CLI, or plugin system
- Performance optimizations
- Security enhancements
- Documentation improvements

### 3. Documentation
- Tutorials and how-to guides
- API documentation
- Troubleshooting guides
- Translation of documentation

## Pull Request Process

### 1. Before Submitting
- [ ] Run the full test suite
- [ ] Ensure code passes linting and type checking
- [ ] Update documentation if needed
- [ ] Add tests for new functionality
- [ ] Consider security implications of changes

### 2. Creating a Pull Request
1. **Title**: Use clear, descriptive title (e.g., "Add GitHub plugin for repository secrets")
2. **Description**: 
   - Explain the purpose of the change
   - Reference related issues
   - Describe testing performed
   - Note any security considerations
3. **Labels**: Add appropriate labels (bug, enhancement, documentation, security, etc.)

### 3. PR Review Criteria
- **Security**: Does the change introduce any security risks?
- **Correctness**: Does the change work as intended?
- **Testing**: Are there adequate tests?
- **Documentation**: Is documentation updated?
- **Code Quality**: Does the code follow project standards?
- **Performance**: Does the change impact performance?

### 4. After Approval
- Maintainer will merge the PR
- Changes will be included in the next release
- Contributors will be credited in release notes

## Security Contributions

### Reporting Security Issues
**DO NOT** create a public issue for security vulnerabilities.

Instead, email security reports to: `security@pitanga.org`

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if known)

### Security Review Process
1. Acknowledgment within 48 hours
2. Investigation and validation
3. Patch development
4. Release of fixed version
5. Public disclosure (if appropriate)

## Community Guidelines

### Code of Conduct
We are committed to providing a friendly, safe, and welcoming environment for all contributors. Please:
- Be respectful and inclusive
- Use welcoming language
- Accept constructive criticism gracefully
- Focus on what is best for the project
- Show empathy towards other community members

### Communication
- Use GitHub Issues for bug reports and feature requests
- Use GitHub Discussions for questions and ideas
- Be patient - maintainers are volunteers
- Provide clear, reproducible examples when reporting issues

## Recognition

Contributors are recognized in:
- Release notes
- Contributors list in README
- Project documentation

## Getting Help

- Check existing documentation
- Search GitHub Issues and Discussions
- Ask in GitHub Discussions
- Email: `contributors@pitanga.org`

## Release Process

### Versioning
We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Cycle
1. Feature freeze
2. Final testing and security review
3. Release candidate
4. Final release
5. Release notes publication

---

Thank you for contributing to making Kimi Secrets Vault more secure, useful, and accessible to developers worldwide!

*Last updated: 2026-02-01*