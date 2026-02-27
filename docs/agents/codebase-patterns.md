# Codebase Patterns

This document records common patterns, conventions, and idioms used throughout the Cutesy codebase.

## Package Structure

**Context**: Single-package Python project — `cutesy/` is the main source

**Structure**:
- `cutesy/__init__.py` - Public API (`HTMLLinter`, `cutesy_core`, `_rust_available`)
- `cutesy/linter.py` - Core linter logic (compiled with mypyc in release builds)
- `cutesy/cli.py` - Command-line interface (compiled with mypyc in release builds)
- `cutesy/rules.py` - Linting/formatting rules
- `cutesy/types.py` - Shared type definitions
- `cutesy/attribute_processors/` - Attribute-specific processing logic
- `cutesy/preprocessors/` - HTML preprocessing logic
- `cutesy/utilities/` - Internal utility functions

**Tests mirror the package**:
- `tests/unit/` - Unit tests for individual functions
- `tests/integration/` - End-to-end tests with real HTML files
- `tests/private/` - Tests targeting private methods (use sparingly)

## Build and Development Workflow

**Full pipeline**: `make` (runs clean → configure → format → lint → check → test)

**Individual steps**:
```bash
make format   # docformatter + ruff format + add-trailing-comma (runs ruff format twice)
make lint     # ruff format --diff + ruff check --diff + flake8
make check    # mypy type checking
make test     # all three test groups + combined coverage report
```

**Format pipeline order** (important — runs in sequence):
1. `docformatter` - Python docstrings
2. `ruff format` - General formatting
3. `ruff check --fix-only` - Auto-fixable lint issues
4. `add-trailing-comma` - Trailing commas on dangling lines
5. `ruff format` again - Re-format after trailing comma additions
6. `ruff check --fix-only` again - Final lint fixes

## Code Style Conventions

**Linting tools**: Ruff (formatting + linting) + Flake8 + mypy

**Configuration files**:
- `ruff.toml` - Ruff configuration
- `setup.cfg` - Flake8 and mypy configuration
- `pyproject.toml` - Additional tool configuration

**Trailing commas**: `add-trailing-comma` is part of the format pipeline — always use trailing commas in multi-line structures.

## Configuration Management

**`configure` target**: Runs `nitpick check` to validate configuration files against a global spec. This runs as part of `make` (full pipeline). If configuration drifts from the spec, `make configure` will report it.

## Performance Extensions

**Two-tier strategy**:
1. **mypyc** (Tier 1): Compiles Python to C extensions — `linter.py` and `cli.py` are compiled
2. **Rust** (Tier 2): Optional hotspot extensions via PyO3/maturin — lives in `rust/`

**Release builds**: `make build` → produces wheel in `dist/` with mypyc + Rust
**Dev builds**: Run source directly (no compilation needed for normal development)

**Rust extension availability**: `cutesy._rust_available` (bool) — code must gracefully handle when Rust is unavailable

## Indentation Stack Logic

**Context**: `linter.py` — how opening/closing tags manage indentation

**Pattern**: Opening tags push a `StackItem` onto `_tag_stack` with the current `_indentation_level`, then increment. Closing tags pop the stack to find the match and restore the saved level.

**Recovery on unmatched close**: Both `handle_endtag()` (HTML tags) and `handle_instruction()` (template instructions) decrement `_indentation_level` by 1 when no matching opening is found, to avoid cascading indentation errors downstream. Guard with `if self._indentation_level > 0`.

**Key locations**:
- `handle_starttag()` — increment at push
- `handle_endtag()` — restore from stack, or decrement-by-1 on D4 error
- `handle_instruction()` — same pattern, P3 error

## Notes to Add

- HTML linting/formatting rule conventions
- Attribute processor patterns
- Preprocessor patterns
- CLI argument handling patterns
