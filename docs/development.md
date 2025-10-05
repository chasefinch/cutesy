# Cutesy Development Guide

## Environment Setup

**Setup development environment:**
```bash
git clone https://github.com/chasefinch/cutesy.git
cd cutesy
make setup
source .venv/bin/activate
```

**Run tests:**
```bash
make format      # Format code
make lint        # Check code style
make test        # Run all tests
make test-unit   # Unit tests only
```

```bash
make             # Run everything
```

**Project requirements:**
- **Python 3.11+** for development
- **uv** for dependency management - `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **mypy** (includes mypyc) - `pip install mypy`
- **Rust 1.70+** (optional, for Rust extensions) - `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- **maturin** (optional, for Rust extensions) - `pip install maturin`

## Performance Extensions

Cutesy uses a two-tier performance optimization strategy:

### Tier 1: mypyc Compilation (Current - 3-5x speedup)

All Python code is compiled to C extensions using mypyc. This is what PyPI and Homebrew users get automatically.

**Development commands:**
```bash
make build    # Build wheel with mypyc + Rust extensions
make clean    # Clean build artifacts
```

The mypyc-compiled code can call Rust extensions when available for additional performance.

**Disabling mypyc:**
```bash
CUTESY_USE_MYPYC=0 pip install -e .
# Or: make build-no-compile
```

### Tier 2: Rust Extensions

For maximum performance, critical hotspot functions can be rewritten in Rust. The mypyc-compiled Python code calls these when available.


**Development commands:**
```bash
make build-extensions              # Dev mode (fast)
make build-extensions release=true # Release mode (wheels + sdist)
make test-extensions               # Test extension loads
make clean-extensions              # Clean artifacts
```

**Project structure:**
```
rust/
├── Cargo.toml       # Rust dependencies
└── src/
    └── lib.rs       # Extension implementation (stub)
```

**Resources:**
- [mypyc Documentation](https://mypyc.readthedocs.io/)
- [PyO3 Documentation](https://pyo3.rs/)
- [Maturin Guide](https://www.maturin.rs/)
- [Profiling Analysis](../PROFILING_ANALYSIS.md)

## Testing Strategy

Cutesy has three types of tests:

### Test Categories

#### Unit Tests (`tests/unit/`)
Test individual functions through their public interfaces. Generally prefer testing private functionality indirectly rather than calling private methods directly.

#### Integration Tests (`tests/integration/`)
End-to-end testing with actual HTML files and expected results. Make sure the system works as a whole with real-world scenarios.

#### Private Tests (`tests/private/`)
Direct testing of private methods when public interface testing isn't enough. Use sparingly - only when unit tests don't provide adequate coverage. The linter allows private member access in `tests/private/` but not elsewhere.

### Running Tests

- `make test-unit` - Run only unit tests
- `make test-integration` - Run only integration tests
- `make test-private` - Run only private unit tests.
- `make test` - Run all tests with combined coverage
- `make test build=True` -

Each test type generates its own coverage data file, then `make test` combines them all.
