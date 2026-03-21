---
name: gh:index
description: プロジェクト構造を最大限調査し、Issue作成の元ネタとなるナレッジインデックスを生成
---

# /gh:index - Project Knowledge Index Generator

> **Concept**: Investigation only. Output serves as source material for Issue creation. No project modifications.

## Usage

```bash
/gh:index [target]    # Analyze target directory (default: current directory)
/gh:index             # Analyze current directory
```

---

## Output

Single file: `claudedocs/project_index.md`

---

## Workflow (4 Phases - Maximum Investigation)

### Phase 1: Discovery (探索)

1. **Full Project Scan**: `list_dir(recursive=true)` via Serena
2. **Technology Detection**:
   - Languages: `.py`, `.ts`, `.js`, `.go`, `.rs`, etc.
   - Frameworks: package.json, pyproject.toml, Cargo.toml
   - Build tools: Makefile, webpack.config, vite.config
3. **Documentation Inventory**: README, docs/, CHANGELOG, API docs
4. **Entry Points**: main.*, index.*, src/*, app/*

```
Serena tools:
- list_dir(".", recursive=true)
- find_file("*.md", ".")
- find_file("pyproject.toml|package.json|Cargo.toml", ".")
```

---

### Phase 2: Deep Analysis (詳細分析)

1. **Symbol Extraction**: `get_symbols_overview()` for all code files
2. **Dependency Mapping**:
   - External: requirements.txt, package.json dependencies
   - Internal: import/require patterns
3. **Architecture Patterns**:
   - MVC, Clean Architecture, Domain-Driven
   - Monolith, Microservices, Monorepo
4. **Quality Metrics**:
   - Type hint coverage (Python: mypy, TS: strict mode)
   - Test coverage (tests/ directory analysis)
   - Docstring/JSDoc coverage
5. **Concerns Detection**:
   - Security: hardcoded secrets, SQL injection patterns
   - Performance: N+1 queries, unbounded loops
   - Technical debt: TODO/FIXME/HACK comments

```
Serena tools:
- get_symbols_overview(relative_path) for each code file
- search_for_pattern("TODO|FIXME|HACK", restrict_search_to_code_files=true)
- search_for_pattern("password|secret|api_key", restrict_search_to_code_files=true)
```

---

### Phase 3: Indexing (インデックス化)

1. **Structure Compilation**: Aggregate all findings into Markdown
2. **Cross-Reference Generation**: Link symbols to their locations
3. **Output Generation**: Write to `claudedocs/project_index.md`

---

### Phase 4: Issue Candidates (Issue候補)

1. **Undocumented Areas**: Files/symbols without docs
2. **Improvement Recommendations**: Quality gaps, missing tests
3. **Technical Debt**: TODO items, deprecated patterns
4. **Priority Classification**: High/Medium/Low based on impact

---

## Output Format: project_index.md

```markdown
# Project Index: {project_name}

Generated: {timestamp}

## Overview

- Language: Python 3.11
- Framework: FastAPI
- Build: uv + pyproject.toml
- Test: pytest

## Directory Structure

├── src/
│   ├── api/       # REST endpoints (12 files)
│   ├── core/      # Business logic (8 files)
│   └── models/    # Data models (5 files)
├── tests/         # Test suite (23 files)
└── docs/          # Documentation (2 files)

## Key Entry Points

| File | Purpose |
|------|---------|
| src/main.py | Application entry |
| src/api/routes.py | Route definitions |
| src/core/config.py | Configuration |

## Core Symbols

| Symbol | Location | Type | Description |
|--------|----------|------|-------------|
| App | src/main.py:15 | Class | Main application |
| UserService | src/core/users.py:28 | Class | User business logic |
| get_user | src/api/users.py:42 | Function | User retrieval endpoint |

## Dependencies

### External

- fastapi: ^0.100.0
- pydantic: ^2.0.0
- sqlalchemy: ^2.0.0

### Internal Module Dependencies

- src/api → src/core → src/models

## Quality Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Type hint coverage | 78% | ⚠️ |
| Test coverage | 65% | ⚠️ |
| Docstring coverage | 45% | ❌ |

## Documentation Status

| Document | Status | Notes |
|----------|--------|-------|
| README.md | ✅ | Exists, up to date |
| API docs | ❌ | Missing |
| Architecture | ❌ | Missing |

## Technical Debt

| Type | Count | Locations |
|------|-------|-----------|
| TODO | 12 | src/core/users.py:45, src/api/auth.py:23, ... |
| FIXME | 3 | src/models/order.py:78, ... |
| HACK | 1 | src/utils/cache.py:15 |

## Security Concerns

| Issue | Severity | Location |
|-------|----------|----------|
| Hardcoded API key | 🚨 High | src/config.py:12 |
| SQL string concat | ⚠️ Medium | src/db/queries.py:34 |

## Issue Candidates

> Issue作成の元ネタ。優先度順。

### High Priority

1. **API Documentation Missing**
   - Target: src/api/ (all files)
   - Impact: Developer onboarding delayed
   - Suggested Issue: "docs: Add OpenAPI documentation for REST endpoints"

2. **Security: Hardcoded Credentials**
   - Target: src/config.py:12
   - Impact: Security vulnerability if committed
   - Suggested Issue: "security: Move credentials to environment variables"

### Medium Priority

3. **Low Type Hint Coverage in core/**
   - Target: src/core/*.py (8 files)
   - Impact: IDE completion disabled, bug risk
   - Suggested Issue: "chore: Add type hints to core business logic"

4. **Test Coverage Gap**
   - Target: src/core/users.py, src/core/orders.py
   - Impact: Refactoring regression risk
   - Suggested Issue: "test: Add unit tests for user and order services"

### Low Priority

5. **Docstring Missing**
   - Target: 55% of codebase
   - Impact: Code comprehension cost
   - Suggested Issue: "docs: Add docstrings to public APIs"

6. **Technical Debt Cleanup**
   - Target: 16 TODO/FIXME/HACK items
   - Impact: Accumulated maintenance burden
   - Suggested Issue: "chore: Address technical debt items"
```

---

## MCP Integration

| Phase | Serena Tool | Purpose |
|-------|-------------|---------|
| Discovery | list_dir | Full directory scan |
| Discovery | find_file | Locate config/doc files |
| Analysis | get_symbols_overview | Extract code symbols |
| Analysis | search_for_pattern | Find patterns/concerns |
| Output | create_text_file | Write project_index.md |

---

## Auto-Detection Rules

### Language Detection

| File Pattern | Language |
|--------------|----------|
| `*.py`, `pyproject.toml` | Python |
| `*.ts`, `*.tsx`, `tsconfig.json` | TypeScript |
| `*.js`, `*.jsx`, `package.json` | JavaScript |
| `*.go`, `go.mod` | Go |
| `*.rs`, `Cargo.toml` | Rust |
| `*.java`, `pom.xml` | Java |

### Framework Detection

| Indicator | Framework |
|-----------|-----------|
| fastapi in deps | FastAPI |
| django in deps | Django |
| flask in deps | Flask |
| react in deps | React |
| vue in deps | Vue |
| next in deps | Next.js |
| express in deps | Express |

---

## Boundaries

### Will Do ✅

- Maximum depth investigation of project structure
- Symbol extraction and dependency analysis
- Quality metrics calculation
- Issue candidate identification with priority
- Output to `claudedocs/project_index.md`

### Will NOT Do ❌

- Modify any project files
- Edit existing documentation
- Create Issues automatically (manual step after review)
- Execute tests or build commands
- Make code changes

---

## Examples

### Basic Usage

```
User: /gh:index

Claude:
1. [Discovery] Scanning project structure...
   - Found: Python project (pyproject.toml)
   - Framework: FastAPI
   - 45 source files, 23 test files

2. [Analysis] Extracting symbols...
   - 12 classes, 45 functions analyzed
   - Type coverage: 78%
   - Test coverage: 65%

3. [Indexing] Generating index...
   - Writing claudedocs/project_index.md

4. [Issue Candidates] 6 candidates identified
   - High: 2 (API docs, security)
   - Medium: 2 (types, tests)
   - Low: 2 (docstrings, tech debt)

✅ Index generated: claudedocs/project_index.md
→ Review candidates and create Issues with /gh:issue create
```

### With Target Directory

```
User: /gh:index src/

Claude:
1. [Discovery] Scanning src/ only...
   ...
```

---

## Related Commands

```bash
/gh:index              # Generate project index (this command)
                       ↓
/gh:issue create       # Create Issue from candidates
                       ↓
/gh:start 42           # Start work on Issue
```

---

## Execution Instructions

**You are now executing `/gh:index`.**

Follow these steps:

1. **Activate Serena** (if not active):
   ```
   activate_project(user's current directory)
   ```

2. **Phase 1 - Discovery**:
   - `list_dir(".", recursive=true)`
   - Detect language/framework from config files
   - Inventory documentation files

3. **Phase 2 - Analysis**:
   - `get_symbols_overview()` for each code file
   - `search_for_pattern()` for TODO/FIXME/security concerns
   - Calculate quality metrics

4. **Phase 3 - Indexing**:
   - Compile findings into Markdown format
   - Ensure `claudedocs/` directory exists
   - Write `claudedocs/project_index.md`

5. **Phase 4 - Issue Candidates**:
   - Prioritize findings by impact
   - Generate suggested Issue titles
   - Include in output file

6. **Report**:
   - Summary of findings
   - Path to generated file
   - Prompt to review and create Issues

---

**Last Updated**: 2026-01-26
**Version**: 1.0.0
