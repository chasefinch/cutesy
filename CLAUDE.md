# Claude Code — Cutesy

A linter & formatter for consistent HTML code. Python package with mypyc + Rust compilation.

## Before You Start

`docs/agents/` contains notes from past sessions that may be relevant to your task. Consult when you need context; update when you learn something non-obvious.

## When You...

- **Learn something non-obvious** → Add a "When You..." entry here (keep this file under 100 lines), or update `docs/agents/`.
- **Run tests or CI commands** → See Quick Reference below
- **Work with the build** → `make build` compiles mypyc + Rust; `make test-build` tests the wheel

## Quick Reference

| Task | Command |
|---|---|
| **Full pipeline** | `make` (format, lint, check, test) |
| **Format** | `make format` |
| **Lint** | `make lint` (format first!) |
| **Type check** | `make check` |
| **Test** | `make test` |
| **Build wheel** | `make build` |
| **Test wheel** | `make test-build` |

Always activate the venv first: `source .venv/bin/activate`

## Skills & Tools

Custom Claude Code skills live in `.claude/skills/`. MCP servers may also be installed at the IDE level — discover available tools before assuming they don't exist.

## Key Directories

- `cutesy/` — Main package source code
- `tests/` — Test files (unit, integration, private)
- `requirements/` — Requirements files
- `rust/` — Rust extension source

## Special Considerations

- This project has multiple test groups (integration, unit, and private). Always run the complete test suite with `make test` when coverage data or validation is needed.

## Agent Notes

`docs/agents/` is the shared knowledge base for all LLM agents. Version-controlled and team-visible. Keep notes accurate, concise, and actionable.
