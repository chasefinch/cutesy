# Claude Code Configuration

This file contains configuration for Claude Code to help with development tasks.

## Agent Learning System

**IMPORTANT**: Before starting any development work, always consult the agent notes in `docs/agents/`. These notes contain accumulated knowledge about patterns, pitfalls, and best practices specific to this codebase.

### Required Workflow for Agents

1. **Read relevant notes first** - Check `docs/agents/INDEX.md` and relevant note files before starting work
2. **Reference notes during development** - Apply patterns and avoid pitfalls documented in the notes
3. **Update notes after learning** - When you discover important patterns, solutions, or pitfalls, update the appropriate note file
4. **Keep notes current** - As you work with the codebase, continuously improve the notes for future sessions. Add and keep important learnings, but be concise and remove outdated or excessive notes.

### Agent Notes Location

See `docs/agents/INDEX.md` for the complete index of agent notes including:
- Codebase patterns and conventions
- Common pitfalls and solutions
- Architecture decisions
- Testing strategies

**Goal**: Build institutional knowledge across development sessions to improve accuracy and speed.

## Project Overview
- **Type**: Python package
- **Name**: Cutesy
- **Description**: A linter & formatter for consistent HTML code

## Commands

### Linting
```bash
make lint
```

### Type Checking
```bash
make check
```

### Testing
```bash
make test
```

### Formatting
```bash
make format
```

### Full Build Pipeline
```bash
make
```

## Project Structure
- `cutesy/` - Main package source code
- `tests/` - Test files
- `requirements/` - Requirements files
- `setup.py` - Package configuration
- `Makefile` - Build commands
- `ruff.toml` - Ruff configuration
- `setup.cfg` - Setup configuration

## Development Workflow
1. Make changes to code
2. Run `make format` to auto-format
3. Run `make lint` to check for issues
4. Run `make check` for type checking
5. Run `make test` to run tests
6. Run `make` to run the full pipeline

## Special Considerations
- This project has multiple test groups (integration, unit, and private). Always run the complete test suite with `make test` when coverage data or validation is needed.

## Developer Documentation
- [Agent Notes Index](docs/agents/INDEX.md) - Agent learning system (read first!)
- [Development Guide](docs/development.md) - Testing strategy and development patterns
