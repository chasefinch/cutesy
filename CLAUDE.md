# Claude Code Configuration

This file contains configuration for Claude Code to help with development tasks.

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

## Developer Documentation
- [Development Guide](docs/development.md) - Testing strategy and development patterns
