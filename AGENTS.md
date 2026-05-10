# Agent Development Guide

**Purpose**: This guide documents the architecture, patterns, and practices used in this project. It serves as both onboarding documentation for AI coding assistants and a template for other projects.

**Status**: Living document — update as patterns evolve

---

## Table of Contents

1. [Git Workflow](#git-workflow)
2. [Project Architecture](#project-architecture)
3. [Testing Strategy](#testing-strategy)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Code Quality Standards](#code-quality-standards)
6. [Documentation Structure](#documentation-structure)
7. [Security Practices](#security-practices)
8. [Common Patterns](#common-patterns)

---

## Git Workflow

### Feature Branch Model

**Never commit directly to `main`**. Always use feature branches:

```bash
# 1. Create feature branch from main
git checkout -b feature/descriptive-name

# 2. Work iteratively, commit as needed
git add <files>
git commit -m "feat: add specific feature"
git commit -m "fix: address edge case"
git commit -m "refactor: simplify logic"

# 3. Push branch to remote
git push origin feature/descriptive-name

# 4. When complete, squash-merge to main for clean history
git checkout main
git pull origin main  # Ensure main is up-to-date
git merge --squash feature/descriptive-name
git commit -m "feat: descriptive summary of entire feature"
git push origin main

# 5. Clean up
git branch -d feature/descriptive-name
git push origin --delete feature/descriptive-name
```

### Why This Workflow?

- **Clean main history**: One commit per feature, easy to review/revert
- **Iterative development**: Branch commits can be WIP, experimental, "oops" fixes
- **Easy collaboration**: Clear separation between work-in-progress and production
- **Atomic changes**: Each main commit represents a complete, tested feature

### Commit Message Conventions

Use semantic prefixes:

| Prefix | Use Case | Example |
|--------|----------|---------|
| `feat:` | New feature | `feat: add GitHub plugin with issue management` |
| `fix:` | Bug fix | `fix: handle expired OAuth tokens gracefully` |
| `docs:` | Documentation only | `docs: update plugin development guide` |
| `test:` | Add/update tests | `test: add unit tests for vault encryption` |
| `refactor:` | Code refactor | `refactor: extract client initialization to helper` |
| `chore:` | Build/tooling | `chore: update dependencies` |
| `perf:` | Performance improvement | `perf: cache OAuth credentials in memory` |

### Force Push Guidelines

Use `git push --force-with-lease` **only** when:
- You are the sole contributor
- Cleaning up main after coordination
- Rebasing feature branch (never rebase shared branches)

**Never** force push to branches others are actively working on.

---

## Project Architecture

### High-Level Structure

This is a **plugin-based CLI tool** with the following layers:

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Layer                             │
│  Entry point: nakimi <plugin>.<command> [args]          │
│  Parse commands, route to plugins                        │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                 Plugin Manager                           │
│  • Auto-discovers plugins                                │
│  • Loads only plugins with credentials                   │
│  • Routes commands to plugin handlers                    │
└─────────────────────────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │ Plugin 1│    │ Plugin 2│    │ Plugin 3│
    │ (gmail) │    │(calendar│    │ (github)│
    └─────────┘    └─────────┘    └─────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   Core Services                          │
│  • Vault (encryption/decryption)                         │
│  • Config (environment + file-based)                     │
│  • Session management                                    │
└─────────────────────────────────────────────────────────┘
```

### Core Patterns

#### Pattern 1: Plugin Auto-Discovery

**Problem**: Need extensibility without manually registering every plugin

**Solution**: Filesystem-based discovery with conditional loading

```python
# src/nakimi/core/plugin.py
class PluginManager:
    def discover_plugins(self):
        """Auto-discover plugins from plugins/ directory"""
        plugin_dir = Path(__file__).parent.parent / "plugins"

        for subdir in plugin_dir.iterdir():
            if not subdir.is_dir() or subdir.name.startswith("_"):
                continue

            # Import the plugin module
            module_path = f"nakimi.plugins.{subdir.name}.plugin"
            try:
                module = importlib.import_module(module_path)

                # Find Plugin subclass
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, Plugin) and obj != Plugin:
                        plugin_name = getattr(obj, "PLUGIN_NAME", subdir.name)

                        # Only load if credentials exist
                        if plugin_name in self.secrets_data:
                            self.register_plugin(obj, self.secrets_data[plugin_name])
            except ImportError as e:
                logger.debug(f"Could not load plugin {subdir.name}: {e}")
```

**Benefits**:
- Drop-in plugins: just add a directory
- Graceful degradation: missing plugins don't break the system
- No central registry to maintain

**Reusable for**: Any plugin-based system (IDE extensions, API integrations, data connectors)

#### Pattern 2: Abstract Base Class for Extensibility

**Problem**: Enforce plugin interface without tight coupling

**Solution**: Use `abc.ABC` to define contract

```python
from abc import ABC, abstractmethod

@dataclass
class PluginCommand:
    """Command descriptor - reusable across plugins"""
    name: str
    description: str
    handler: Callable[..., Any]
    args: List[Tuple[str, str, bool]]  # (name, help, required)

class Plugin(ABC):
    """Base class all plugins must implement"""

    PLUGIN_NAME: str = ""  # Override in subclass

    def __init__(self, secrets: Dict[str, Any]):
        self.secrets = secrets
        self._validate_secrets()  # Enforce validation

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable plugin description"""
        pass

    @abstractmethod
    def _validate_secrets(self):
        """Raise PluginError if secrets are invalid"""
        pass

    @abstractmethod
    def get_commands(self) -> List[PluginCommand]:
        """Return list of commands this plugin provides"""
        pass
```

**Benefits**:
- Type safety: IDE autocomplete for required methods
- Fail fast: missing methods caught at import time
- Self-documenting: interface is the documentation

**Reusable for**: Any system requiring multiple implementations of a common interface

#### Pattern 3: Lazy Initialization

**Problem**: Plugins may have expensive setup (OAuth handshake, API connections)

**Solution**: Initialize on first use, not in `__init__`

```python
class GmailPlugin(Plugin):
    def __init__(self, secrets: Dict[str, Any]):
        self.client = None  # Don't initialize here
        super().__init__(secrets)

    def _get_client(self) -> GmailClient:
        """Lazy-load client on first command"""
        if self.client is None:
            self.client = GmailClient(self.secrets)
            # OAuth handshake happens here
        return self.client

    def cmd_unread(self, limit: str = "10") -> str:
        client = self._get_client()  # Initialize only when needed
        return client.list_unread(int(limit))
```

**Benefits**:
- Faster startup: plugins load instantly
- Resource efficiency: unused plugins don't consume resources
- Better error handling: connection errors happen during command execution

**Reusable for**: Database connections, API clients, ML model loading

#### Pattern 4: Context Managers for Cleanup

**Problem**: Temporary files, connections, or resources must be cleaned up even on error

**Solution**: Use `@contextlib.contextmanager` for guaranteed cleanup

```python
import contextlib

@contextlib.contextmanager
def _with_decrypted_key(self):
    """Ensure temporary key files are always cleaned up"""
    key_path = self._get_decrypted_key_path()
    try:
        yield key_path
    finally:
        # Cleanup happens even if code inside context raises
        if key_path != self.key_file and key_path.exists():
            secure_delete(key_path)

# Usage:
def decrypt(self, ciphertext_path: Path) -> Path:
    with self._with_decrypted_key() as key_path:
        subprocess.run(["age", "-d", "-i", str(key_path), ...])
    # key_path is guaranteed to be cleaned up
```

**Benefits**:
- Exception-safe: cleanup always happens
- Resource leak prevention: no forgotten cleanup
- Readable: clear entry/exit points

**Reusable for**: Database transactions, file locks, temp files, API sessions

#### Pattern 5: Secure Fallbacks

**Problem**: Security features may not work in all environments (containers, different OSes)

**Solution**: Prioritize security, fallback gracefully

```python
def get_secure_temp_dir() -> Optional[Path]:
    """Get best available temp directory

    Priority:
    1. /dev/shm (RAM, Linux) - secrets never hit disk
    2. /private/tmp (macOS) - usually RAM-backed
    3. None (system default) - fallback to /tmp
    """
    # Linux: /dev/shm is RAM-backed tmpfs
    if platform.system() == "Linux":
        shm_path = Path("/dev/shm")
        if shm_path.exists() and shm_path.is_dir():
            try:
                # Test writability
                test_file = shm_path / f".{PROJECT_NAME}-test"
                test_file.touch()
                test_file.unlink()
                return shm_path
            except (PermissionError, OSError):
                pass  # Fall through to next option

    # macOS: /private/tmp
    if platform.system() == "Darwin":
        mac_tmp = Path("/private/tmp")
        if mac_tmp.exists():
            return mac_tmp

    # Fallback: use system default
    return None

def secure_delete(file_path: Path):
    """Delete file securely based on filesystem type"""
    if not file_path.exists():
        return

    # On RAM disk: plain delete (data never hit physical disk)
    if is_ram_disk(file_path):
        file_path.unlink()
        return

    # On physical storage: overwrite before deleting
    try:
        subprocess.run(["shred", "-u", str(file_path)], check=True)
    except FileNotFoundError:
        # macOS doesn't have shred - fallback
        file_path.unlink()
```

**Benefits**:
- Works everywhere: graceful degradation
- Best effort security: uses strongest available option
- Clear documentation: comments explain priority

**Reusable for**: Cross-platform utilities, optional hardware support, tiered caching

---

## Testing Strategy

### Testing Philosophy

1. **Test behavior, not implementation**: Verify what code does, not how
2. **Mock external dependencies**: Never test real APIs, filesystems, or encryption
3. **Isolate tests**: Each test starts fresh (no shared state)
4. **Cover edge cases**: Test both success and failure paths

### Test Organization

```
tests/
├── conftest.py          # Shared fixtures (temp_dir, mock_vault, etc.)
├── unit/                # Fast, isolated tests (no I/O)
│   ├── test_vault.py
│   ├── test_plugin.py
│   └── test_config.py
├── integration/         # Test component interactions
│   ├── test_cli.py
│   └── test_gmail_plugin.py
└── fixtures/            # Test data files
```

### Essential Fixtures

**File**: `tests/conftest.py`

```python
import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def temp_dir():
    """Isolated temp directory for each test"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def test_config(temp_dir):
    """Reset global config, use temp paths"""
    reset_config()  # Clear any cached config
    os.environ["PROJECT_DIR"] = str(temp_dir / ".project")
    os.environ["PROJECT_KEY"] = str(temp_dir / ".project" / "key.txt")
    return get_config()

@pytest.fixture
def mock_secrets():
    """Fake credentials for testing"""
    return {
        "gmail": {
            "client_id": "test-client-id",
            "client_secret": "test-secret",
            "refresh_token": "test-token",
        }
    }

@pytest.fixture
def patch_external_commands():
    """Mock subprocess calls to external tools"""
    with patch("subprocess.run") as mock_run:
        def side_effect(cmd, *args, **kwargs):
            if "external-tool" in cmd:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = b"expected output"
                return mock_result
            raise FileNotFoundError(f"Unmocked command: {cmd}")

        mock_run.side_effect = side_effect
        yield mock_run
```

### Mocking Patterns

#### Pattern: Mock File Operations

```python
from unittest.mock import mock_open, patch

def test_read_config():
    mock_file_content = 'key=value\n'
    mock_file = mock_open(read_data=mock_file_content)

    with patch('builtins.open', mock_file):
        config = load_config('/path/to/config')

    assert config['key'] == 'value'
```

#### Pattern: Mock Path Objects

```python
from unittest.mock import Mock
from pathlib import Path

def test_file_exists():
    mock_path = Mock(spec=Path)
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = True

    result = process_file(mock_path)

    assert result is not None
```

#### Pattern: Mock External API Clients

```python
@patch('project.plugins.api.APIClient')
def test_api_plugin_command(mock_client_class):
    # Set up mock
    mock_client = Mock()
    mock_client.fetch_data.return_value = [{"id": 1, "name": "Test"}]
    mock_client_class.return_value = mock_client

    # Test
    plugin = APIPlugin({"api_key": "test"})
    result = plugin.cmd_list()

    # Verify
    assert "Test" in result
    mock_client.fetch_data.assert_called_once()
```

### Test Coverage Goals

| Component | Target Coverage | Rationale |
|-----------|----------------|-----------|
| Core (vault, config) | 90%+ | Critical security/reliability |
| Plugin base | 85%+ | Affects all plugins |
| Individual plugins | 70%+ | Integration code, harder to test |
| CLI | 60%+ | Hard to test, covered by integration tests |

**Check coverage**: `pytest --cov=src --cov-report=term-missing`

### Running Tests

```bash
# All tests
pytest

# Unit tests only (fast)
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Specific test file
pytest tests/unit/test_vault.py

# Specific test
pytest tests/unit/test_vault.py::TestVault::test_encrypt_success

# With coverage
pytest --cov=src --cov-report=html
```

---

## CI/CD Pipeline

### GitHub Actions Workflows

**File**: `.github/workflows/test.yml`

```yaml
name: Test Suite

on:
  push:
    branches: [main]
    paths-ignore: ['docs/**']
  pull_request:
    branches: [main]
  workflow_dispatch:  # Allow manual trigger

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ["3.9", "3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install system dependencies
      run: |
        # Example: install age encryption tool
        if [ "$RUNNER_OS" == "Linux" ]; then
          wget -q https://github.com/FiloSottile/age/releases/download/v1.2.0/age-v1.2.0-linux-amd64.tar.gz
          tar -xzf age-v1.2.0-linux-amd64.tar.gz
          sudo mv age/age /usr/local/bin/
        elif [ "$RUNNER_OS" == "macOS" ]; then
          brew install age
        fi

    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev]

    - name: Run tests
      run: pytest --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
        fail_ci_if_error: false

  style-check:
    runs-on: ubuntu-latest
    needs: test  # Only run if tests pass

    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.12"

    - name: Install dependencies
      run: |
        pip install black flake8 mypy

    - name: Check formatting
      run: black --check src/ tests/

    - name: Lint
      run: flake8 src/ tests/ --max-line-length=110

    - name: Type check
      run: mypy src/
```

### Documentation Deploy

**File**: `.github/workflows/pages.yml`

```yaml
name: Deploy Documentation

on:
  push:
    branches: [main]
    paths: ['docs/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./docs
```

### Git Hooks

#### Pre-commit Hook

**File**: `hooks/pre-commit`

```bash
#!/bin/bash
# Run quick tests before allowing commit

echo "🔍 Running pre-commit checks..."

# Check if any Python files are staged
PYTHON_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

if [ -z "$PYTHON_FILES" ]; then
    echo "✅ No Python files staged - skipping tests"
    exit 0
fi

# Run tests on staged files
python -m pytest tests/ -q

if [ $? -ne 0 ]; then
    echo "❌ Tests failed - commit blocked"
    exit 1
fi

echo "✅ Pre-commit checks passed"
exit 0
```

#### Pre-push Hook

**File**: `hooks/pre-push`

```bash
#!/bin/bash
# Run full test suite before allowing push

echo "🔍 Running pre-push validation..."

# Run full test suite
python -m pytest tests/ -v

if [ $? -ne 0 ]; then
    echo "❌ Test failures detected - push blocked"
    echo "Fix tests or use --no-verify to skip (not recommended)"
    exit 1
fi

echo "✅ All tests passed - allowing push"
exit 0
```

**Install hooks**: Copy to `.git/hooks/` and `chmod +x`

---

## Code Quality Standards

### Black (Formatting)

**Configuration**: `pyproject.toml`

```toml
[tool.black]
line-length = 110
target-version = ['py39', 'py310', 'py311', 'py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.venv
  | build
  | dist
)/
'''
```

**Run**: `black src/ tests/`

### Flake8 (Linting)

**Configuration**: `.flake8` or `setup.cfg`

```ini
[flake8]
max-line-length = 110
max-complexity = 10
exclude = .git,__pycache__,build,dist,.venv
ignore = E203, W503  # Black compatibility
```

**Run**: `flake8 src/ tests/`

### MyPy (Type Checking)

**Configuration**: `pyproject.toml`

```toml
[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true  # All functions must have type hints
ignore_missing_imports = false

[[tool.mypy.overrides]]
module = "external_library.*"
ignore_missing_imports = true
```

**Run**: `mypy src/`

### Pytest (Testing)

**Configuration**: `pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "integration: integration tests (slower)",
    "slow: slow tests (skip with -m 'not slow')",
    "hardware: requires specific hardware (e.g., YubiKey)"
]
```

**Run**: `pytest`

### Pre-commit Checklist

Before committing:

```bash
# 1. Format code
black src/ tests/

# 2. Lint
flake8 src/ tests/

# 3. Type check
mypy src/

# 4. Run tests
pytest

# 5. Check coverage
pytest --cov=src --cov-report=term-missing
```

Or use a combined script: `./scripts/quality-check.sh`

---

## Documentation Structure

### Documentation Layout

```
docs/
├── index.md                    # Homepage - project overview
├── getting-started/
│   ├── index.md               # Getting started guide
│   └── installation.md        # Detailed installation
├── guides/                     # User guides
│   ├── feature-1.md
│   └── feature-2.md
├── api/
│   └── index.md               # API reference
├── development/
│   ├── architecture.md        # System design
│   ├── contributing.md        # How to contribute
│   ├── testing.md             # Testing guide
│   └── adr/                   # Architecture Decision Records
│       ├── 001-choice-1.md
│       └── 002-choice-2.md
└── _config.yml                # Jekyll config for GitHub Pages
```

### Architecture Decision Records (ADRs)

Document significant decisions with ADRs:

**Template**: `docs/development/adr/NNN-title.md`

```markdown
# ADR-NNN: Title of Decision

**Status**: Proposed | Accepted | Deprecated | Superseded by ADR-XXX
**Date**: YYYY-MM-DD
**Deciders**: [Names]

## Context

[Describe the issue/problem requiring a decision]

## Decision

[State the decision clearly]

## Consequences

**Positive**:
- Benefit 1
- Benefit 2

**Negative**:
- Trade-off 1
- Trade-off 2

## Alternatives Considered

### Alternative 1
- Pro: ...
- Con: ...

### Alternative 2
- Pro: ...
- Con: ...
```

**Example ADRs in this project**:
- ADR-001: Why age over GPG?
- ADR-002: Plugin auto-discovery pattern
- ADR-003: Just-in-time decryption strategy

---

## Security Practices

### Threat Model

Document what you **do** and **don't** protect against:

**In Scope**:
- Credentials stolen from disk at rest
- Credentials leaked via temp files
- Unauthorized local access to credentials

**Out of Scope**:
- Memory dumps from compromised OS
- Root/administrator access
- Physical access to machine
- Keyloggers

### Security Controls

| Threat | Control | Implementation |
|--------|---------|----------------|
| Data at rest | Encryption | age with public-key cryptography |
| Key compromise | File permissions | `chmod 600` on private keys |
| Temp file leakage | RAM-backed storage | `/dev/shm` preferred, fallback to `/tmp` |
| Temp file recovery | Secure deletion | `shred -u` on physical storage |
| Unauthorized access | No remote access | Local-only tool |

### Secure Coding Checklist

- [ ] No hardcoded credentials (use environment variables or config files)
- [ ] Sensitive data encrypted at rest
- [ ] Temporary files have restricted permissions (`chmod 600`)
- [ ] Secure deletion for sensitive temp files
- [ ] No sensitive data in logs
- [ ] Input validation on all user inputs
- [ ] Avoid shell injection (use `subprocess` with lists, not strings)
- [ ] Dependencies pinned to specific versions

### Example: Secure Temp File Handling

```python
def create_secure_temp_file(prefix: str, suffix: str) -> Path:
    """Create temp file with secure permissions"""
    # Prefer RAM-backed directory
    temp_dir = get_secure_temp_dir() or tempfile.gettempdir()

    fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=temp_dir)
    os.close(fd)
    temp_path = Path(path)

    # Secure permissions
    os.chmod(temp_path, 0o600)

    # Try to lock in memory (best effort)
    if can_mlock():
        mlock_file(temp_path)

    return temp_path
```

---

## Common Patterns

### Pattern: Priority-Based Configuration

```python
class Config:
    def _get_value(self, env_var: str, config_key: str, default: Any) -> Any:
        """Priority: Environment > Config File > Default"""
        # 1. Check environment variable
        if env_var in os.environ:
            return os.environ[env_var]

        # 2. Check config file
        if config_key in self.config_data:
            return self.config_data[config_key]

        # 3. Use default
        return default
```

### Pattern: Dataclass for Structured Data

```python
from dataclasses import dataclass
from typing import Callable, List, Tuple

@dataclass
class Command:
    """Clear structure, IDE autocomplete, validation"""
    name: str
    description: str
    handler: Callable[..., Any]
    args: List[Tuple[str, str, bool]]  # (name, help, required)
```

### Pattern: Factory Functions

```python
def create_plugin(plugin_name: str, secrets: dict) -> Plugin:
    """Factory function for plugin creation"""
    plugin_classes = {
        "gmail": GmailPlugin,
        "github": GitHubPlugin,
        "calendar": CalendarPlugin,
    }

    plugin_class = plugin_classes.get(plugin_name)
    if not plugin_class:
        raise ValueError(f"Unknown plugin: {plugin_name}")

    return plugin_class(secrets)
```

### Pattern: Singleton for Global State

```python
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """Get or create global config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reset_config():
    """Reset for testing"""
    global _config_instance
    _config_instance = None
```

---

## Development Workflow

### Setting Up Development Environment

```bash
# 1. Clone repository
git clone <repo-url>
cd <repo-name>

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install in editable mode with dev dependencies
pip install -e .[dev]

# 4. Install git hooks
cp hooks/pre-commit .git/hooks/
cp hooks/pre-push .git/hooks/
chmod +x .git/hooks/pre-commit .git/hooks/pre-push

# 5. Verify setup
pytest
black --check src/ tests/
flake8 src/ tests/
mypy src/
```

### Daily Development Loop

```bash
# 1. Pull latest changes
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Make changes, test frequently
<edit code>
pytest  # Run tests
black src/ tests/  # Format
flake8 src/ tests/  # Lint

# 4. Commit incrementally
git add <files>
git commit -m "feat: descriptive message"

# 5. When ready, merge to main
git checkout main
git merge --squash feature/my-feature
git commit -m "feat: complete feature description"
git push origin main

# 6. Delete feature branch
git branch -d feature/my-feature
```

### Adding a New Plugin (Example)

```bash
# 1. Create plugin directory
mkdir -p src/nakimi/plugins/newplugin
touch src/nakimi/plugins/newplugin/__init__.py

# 2. Create plugin class
cat > src/nakimi/plugins/newplugin/plugin.py << 'EOF'
from nakimi.core.plugin import Plugin, PluginCommand, PluginError

class NewPlugin(Plugin):
    PLUGIN_NAME = "newplugin"

    @property
    def description(self) -> str:
        return "Description of new plugin"

    def _validate_secrets(self):
        required = ['api_key']
        missing = [f for f in required if not self.secrets.get(f)]
        if missing:
            raise PluginError(f"Missing: {missing}")

    def get_commands(self):
        return [
            PluginCommand("list", "List items", self.cmd_list, [])
        ]

    def cmd_list(self) -> str:
        return "List of items"
EOF

# 3. Add tests
mkdir -p tests/unit/plugins
cat > tests/unit/plugins/test_newplugin.py << 'EOF'
from nakimi.plugins.newplugin.plugin import NewPlugin

def test_newplugin_init():
    plugin = NewPlugin({"api_key": "test"})
    assert plugin.description == "Description of new plugin"
EOF

# 4. Run tests
pytest tests/unit/plugins/test_newplugin.py

# 5. Update documentation
echo "Add plugin docs to docs/guides/newplugin.md"
```

---

## Reusing This Guide for Other Projects

### Quick Adaptation Checklist

When creating a new project, adapt this guide by:

1. **Replace project-specific names**: `nakimi` → `your-project`
2. **Update architecture diagram**: Adjust to your system design
3. **Modify plugin patterns**: If not plugin-based, replace with your extensibility pattern
4. **Keep testing strategy**: The fixtures and mocking patterns are universal
5. **Keep CI/CD structure**: Adjust for your language/framework
6. **Keep git workflow**: Feature branches work for any project
7. **Keep ADRs**: Document your architectural decisions
8. **Update security section**: Define your threat model

### Sections to Always Keep

- Git workflow
- Testing strategy and fixtures
- CI/CD pipeline structure
- Code quality standards
- Documentation structure with ADRs
- Common patterns (configuration, lazy loading, context managers)

### Sections to Customize

- Project architecture (specific to your design)
- Plugin patterns (if not plugin-based)
- Security practices (your threat model)
- Development workflow (language-specific setup)

---

## Maintenance

### Updating This Guide

This document should be updated when:

- A new architectural pattern is introduced
- A testing pattern proves useful
- CI/CD configuration changes
- A significant architectural decision is made (add an ADR)

**Ownership**: Maintainers are responsible for keeping this guide current

---

**Last Updated**: 2026-02-06
**Template Version**: 1.0
**Maintained by**: Andre Pitanga
