# Git Hooks for Test Protection

This project includes git hooks to ensure code quality and prevent pushing broken code to remote repositories.

## Available Hooks

### 1. Pre-push Hook (`/.git/hooks/pre-push`)
**Purpose**: Runs the full test suite before allowing pushes to remote repositories.

**What it does**:
- Runs all tests (`python -m pytest tests/ -v`)
- Blocks push if any tests fail
- Shows detailed test failure information
- Provides helpful error messages and commands to fix issues

**When it runs**: Automatically before `git push`

**To skip temporarily**: `git push --no-verify`

### 2. Pre-commit Hook (`/.git/hooks/pre-commit`)
**Purpose**: Runs quick tests on staged Python files before allowing commits.

**What it does**:
- Checks if staged files include Python files
- Runs tests on any staged test files
- Blocks commit if staged test files fail
- Skips if no Python files are staged

**When it runs**: Automatically before `git commit`

**To skip temporarily**: `git commit --no-verify`

## How the Hooks Work Together

```
Developer makes changes
        ↓
git add <files>           # Stage changes
        ↓
git commit               → pre-commit hook runs quick tests
        ↓                 (catches test failures early)
git push                 → pre-push hook runs full test suite
        ↓                 (final validation before remote)
Remote repository        # Only receives validated code
```

## Benefits

1. **Prevents broken code from leaving workstation** - The pre-push hook ensures all tests pass before code reaches remote repositories
2. **Early detection** - The pre-commit hook catches test failures as soon as changes are staged
3. **Clear feedback** - Both hooks provide detailed error messages and suggestions
4. **Flexible** - Can be skipped with `--no-verify` when needed
5. **Automatic** - No manual steps required for developers

## Installation

The hooks are automatically installed in the `.git/hooks/` directory. They are executable scripts that git runs automatically.

To verify installation:
```bash
ls -la .git/hooks/pre-*
```

Should show:
```
-rwxr-xr-x 1 user user 1234 Feb  1 12:00 .git/hooks/pre-commit
-rwxr-xr-x 1 user user 2345 Feb  1 12:00 .git/hooks/pre-push
```

## Testing the Hooks

### Test pre-push hook:
```bash
# Run manually to see output
.git/hooks/pre-push

# Or try a push (should succeed since tests pass)
git push
```

### Test pre-commit hook:
```bash
# Stage a test file
git add tests/integration/test_cli.py

# Try to commit (should succeed)
git commit -m "Test commit"
```

## Customization

### Modify test command:
Edit `.git/hooks/pre-push` and change the test command:
```bash
# Current line (line ~40):
TEST_OUTPUT=$(python -m pytest tests/ -v 2>&1)

# Change to add coverage:
TEST_OUTPUT=$(python -m pytest tests/ --cov=src/kimi_vault -v 2>&1)
```

### Add linting to pre-commit:
Edit `.git/hooks/pre-commit` to add lint checks:
```bash
# Add after test checks
echo "Running flake8..."
if ! flake8 $PYTHON_FILES; then
    echo "❌ Linting failed"
    exit 1
fi
```

## Troubleshooting

### Hook not running:
1. Check file permissions: `chmod +x .git/hooks/pre-*`
2. Verify git version: `git --version`
3. Check git config: `git config core.hooksPath`

### Tests pass locally but hook fails:
1. Check environment differences
2. Run hook manually: `.git/hooks/pre-push`
3. Check for test dependencies

### Need to skip hooks:
```bash
# Skip pre-commit
git commit --no-verify -m "Emergency fix"

# Skip pre-push  
git push --no-verify
```

## Best Practices

1. **Don't disable hooks** - They protect code quality
2. **Fix test failures immediately** - Don't use `--no-verify` to push broken code
3. **Run hooks locally first** - Test changes before committing
4. **Keep hooks simple** - They should run quickly
5. **Document any skips** - If you use `--no-verify`, document why

## Security Note

These hooks run arbitrary code. Only install hooks from trusted sources. Review the hook scripts before making them executable.

---

**Last updated**: 2026-02-01