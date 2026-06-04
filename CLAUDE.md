# Claude Code — Cutesy

A linter & formatter for consistent HTML code. Pure Python package (no framework/DB/async),
distributed as compiled wheels.

## Commands

Always activate the venv first: `source .venv/bin/activate`

| Task | Command |
|---|---|
| **Full pipeline** (clean → configure → format → lint → check → test) | `make` |
| **Format** | `make format` |
| **Lint** | `make lint` (format first!) |
| **Type check** | `make check` (mypy) |
| **Test** (all groups + combined coverage) | `make test` |
| **Test one group** (faster feedback) | `make test-unit` / `make test-integration` / `make test-private` |
| **Build wheel** | `make build` (mypyc + Rust) |
| **Test wheel** | `make test-build` |

## Key Directories

- `cutesy/` — source. `linter.py` (core), `cli.py`, `rules.py`, `types.py`,
  `attribute_processors/`, `preprocessors/`, `utilities/`. `tailwind.py` defines class-group ordering.
- `tests/` — `unit/` (via public interfaces), `integration/` (real HTML in/out),
  `private/` (direct private-method tests, used sparingly)
- `requirements/`, `rust/` (PyO3/maturin extension)

## How It Works

- **Two-tier perf**: mypyc compiles all Python to C at release time (~3-5x); Rust handles
  hotspots (`rust/`). Dev runs uncompiled source. Code checks `cutesy._rust_available` and must
  fall back gracefully — **always keep the pure-Python path correct**. Some bugs only manifest in
  the compiled wheel, so validate with `make test-build` before release.
- **Config validation**: `make configure` runs `nitpick check` against a shared spec to keep
  `ruff.toml`, `setup.cfg`, `pyproject.toml` in sync. Don't change config files without knowing
  what the spec requires.

## Gotchas

- **`make format` is a multi-pass sequence** (docformatter → ruff format → ruff check fix →
  add-trailing-comma → ruff format → ruff check fix). Don't run formatters individually — use the
  target. `make lint` is read-only (`--diff`) and fails if formatting isn't already applied.
- **Coverage**: combined must be ≥ 91% or `make test` fails. `coverage report -m` shows gaps.
- **Private member access** is allowed only in `tests/private/`; using it in `tests/unit/` or
  `tests/integration/` fails lint.
- **Always use trailing commas** in multi-line structures (`add-trailing-comma` enforces it).

### WPS lint traps (flake8-wps)

- **WPS110** bans names like `val`, `var`, `data`, `result`, `item`, `index`, `value`, `node`,
  `element`, `handler` (and short `i`/`j`/`g` via WPS111). Use domain-specific names.
- **WPS117**: `cls` is reserved even as a comprehension variable — rename.
- **WPS338**: public methods before private; in tests, `setup_method` → `test_*` → `_helpers`.
- **WPS504**: invert negated `if x is not None` conditions (swap branches).
- **WPS600**: can't subclass builtins — use `collections.UserList`/`UserDict`. Note `UserList` is
  not a `list` at runtime (`isinstance(x, list)` is `False`).

### mypy

- `list` is invariant: `list[list[str]]` is not a `list[list[str] | SuperGroup]`, and all-string
  tuples won't satisfy a `str | None` tuple param. Annotate the variable explicitly.
