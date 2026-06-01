# Contributing to TuiCode

Thank you for your interest in contributing! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/wuguirong/tuicode.git
cd tuicode
pip install -e ".[dev]"
```

Run tests:

```bash
PYTHONPATH=src pytest -q
```

## Before Submitting

- All tests must pass (`pytest -q`)
- Keep the scope of changes focused — don't refactor unrelated code in the same PR
- For new features, add a corresponding test under `tests/`

## Bug Reports

Open an Issue with:
1. Steps to reproduce
2. Expected behavior
3. Actual behavior (paste terminal output or screenshot)
4. OS + Python version + Textual version

## Feature Requests

Open an Issue describing the problem you're trying to solve, not just the solution. Features that align with the core principle — **agents as first-class citizens** — are prioritized.

## Pull Requests

- One feature or fix per PR
- Reference the related Issue in the PR description
- PR title format: `feat: short description` / `fix: short description`

## Architecture Constraints

Before writing code, read [CLAUDE.md](CLAUDE.md) for non-negotiable design constraints. In particular:

- 100% TUI — no GUI, no web, no Electron
- New agents must implement the `AgentAdapter` protocol
- Module communication goes through the event bus only
- The workspace state aggregator is the single source of truth for project state

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
