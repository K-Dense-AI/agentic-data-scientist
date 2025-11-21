# Contributing to Agentic Data Scientist

Thanks for your interest in contributing!

## Getting Started

1. Fork and clone the repository
2. Install dependencies: `uv sync --extra dev`
3. Make your changes
4. Run tests: `uv run pytest tests/ -v`
5. Submit a pull request

## Code Style

- Use Python 3.12+ features
- Add type hints
- Write docstrings in NumPy style
- Run `uv run ruff format .` and `uv run ruff check .`

## Commit Messages

Use conventional commits format for clear changelogs:

```
feat: add new feature
fix: resolve bug
docs: update documentation
chore: maintenance tasks
```

Examples:
- `feat: add PostgreSQL support`
- `fix: handle empty files correctly`
- `docs: update README installation steps`

## Questions?

Open an issue or check existing documentation in `docs/`.
