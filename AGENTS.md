# Agent Guidelines for Nakimi

## Git Workflow

### ⚠️ IMPORTANT: Use Feature Branches

**Never commit directly to `main`**. Always use feature branches:

```bash
# 1. Create a feature branch
git checkout -b feature/descriptive-name

# 2. Do your work, commit as needed
git add .
git commit -m "feat: add new feature"

# 3. Push the branch
git push origin feature/descriptive-name

# 4. When ready to merge, squash to keep history clean
git checkout main
git merge --squash feature/descriptive-name
git commit -m "feat: descriptive commit message"
git push origin main

# 5. Clean up
git branch -d feature/descriptive-name
```

### Why?
- Keeps `main` history clean and professional
- Allows iterative commits during development
- Easy to review changes before merging
- Avoids polluting history with "fix", "wip", "oops" commits

### When is Force Push Acceptable?

Only use `git push --force-with-lease` when:
- Cleaning up history on `main` (as we did with the rebase)
- You're the sole contributor and no one else has pulled
- You've coordinated with other contributors

**Never force push to shared branches others are working on.**

## Code Style

- Run `black src/ tests/` before committing
- Run `flake8 src/ tests/` to check linting
- Run `pytest` to ensure tests pass
- Keep commits focused on a single logical change

## Project Structure

- `src/nakimi/` - Core library code
- `tests/` - Test suite
- `docs/` - Documentation
- `.github/workflows/` - CI/CD configuration
