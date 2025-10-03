# Cutesy Development Guide

## Environment Setup

**Setup development environment:**
```bash
git clone https://github.com/chasefinch/cutesy.git
cd cutesy
make setup
source bin/activate
```

**Run tests:**
```bash
make test        # Run all tests
make test-unit   # Unit tests only
make lint        # Check code style
make format      # Format code
```

```bash
make             # Run everything
```

**Project requirements:**
- **Python 3.11+** for development
- **uv** for dependency management - `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Rust 1.70+** (optional, for extensions) - `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- **maturin** (optional, for extensions) - `pip install maturin`

## Rust Extensions

Cutesy includes optional Rust extensions for performance-critical code paths. Users installing from PyPI or Homebrew automatically get pre-compiled wheels with extensions included.

**Development commands:**
```bash
make build-extensions              # Dev mode (fast)
make build-extensions release=true # Release mode (wheels + sdist)
make test-extensions               # Test extension loads
make clean-extensions              # Clean build artifacts
```

**Project structure:**
```
rust/
├── Cargo.toml       # Rust dependencies
└── src/
    └── lib.rs       # Extension implementation
```

**Optimization targets** (from profiling):
- `handle_data()` - 23ms (15% of runtime)
- `goahead()` - 9ms (6% of runtime)  
- `attr_sort()` - 7ms (5% of runtime)

Expected speedup: 5-10x overall

**Resources:**
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

Each test type generates its own coverage data file, then `make test` combines them all.
