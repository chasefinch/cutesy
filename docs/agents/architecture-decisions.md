# Architecture Decisions

This document records key architectural decisions and their context.

## Two-Tier Performance Strategy

**Decision**: Use mypyc (Tier 1) + optional Rust extensions (Tier 2) for performance

**Context**: Cutesy is a linter/formatter that must be fast on large HTML codebases. Pure Python is too slow at scale.

**Tier 1 — mypyc**: All Python source is compiled to C extensions at release time. `linter.py` and `cli.py` are the primary compiled modules. Provides ~3-5x speedup over pure Python with no source changes required.

**Tier 2 — Rust**: Critical hotspot functions can be rewritten in Rust via PyO3/maturin. Lives in `rust/`. Python code checks `_rust_available` and falls back gracefully when Rust extensions aren't present.

**Impact**: Development runs on uncompiled Python source. Releases (PyPI, Homebrew) ship compiled wheels. Always ensure the pure-Python path works correctly — don't assume Rust is available.

## Three-Group Test Architecture

**Decision**: Split tests into unit, integration, and private groups with separate coverage data files

**Rationale**:
- **Unit** (`tests/unit/`): Fast, isolated tests via public interfaces — run often during development
- **Integration** (`tests/integration/`): End-to-end tests with real HTML files — catch regressions
- **Private** (`tests/private/`): Direct private-method tests — used sparingly when public interface testing isn't sufficient; linter relaxes private-access rules only here

**Coverage**: Each group generates its own `.coverage.*` file; `make test` combines them and enforces a 91% minimum threshold.

## Configuration Validation via Nitpick

**Decision**: Use `nitpick` to validate configuration files against a shared global spec

**Context**: Ensures `ruff.toml`, `setup.cfg`, `pyproject.toml`, etc. stay in sync with project standards. Runs as part of the full `make` pipeline via `make configure`.

**Impact**: If configuration drifts, `make configure` will fail. Don't modify config files without understanding what the nitpick spec requires.

## Single Package, No Django/Framework

**Decision**: Pure Python package — no web framework, no ORM, no async

**Context**: Cutesy is a CLI tool and importable library for HTML linting/formatting. Keeping it framework-free keeps it lightweight and universally installable.

**Impact**: No database, no settings module, no middleware. Distribution is a simple pip-installable wheel.

## Notes to Add

- HTML parsing approach (which parser is used, why)
- Rule system design (how rules are registered/applied)
- CLI design decisions
- Attribute processor architecture rationale
