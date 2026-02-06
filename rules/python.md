---
paths:
  - "**/*.py"
---

# Python Rules

## uv Projects
- Always use `uv run python` or `uv run script.py` in projects with pyproject.toml
- Never use `python` or `python3` directly
- Applies to all: ad-hoc scripts, debugging, testing, temporary executions

## Quick Commands
```bash
uv run ruff check src/ --fix
uv run ruff format src/
uv run mypy src/
```
