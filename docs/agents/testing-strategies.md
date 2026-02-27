# Testing Strategies

This document records testing approaches and patterns specific to the Cutesy codebase.

## Test Configuration

**Framework**: pytest with coverage.py

**Minimum Coverage**: 91% threshold (enforced by `make test`)

**Coverage files**: Each group writes its own `.coverage.<group>` file; `make test` combines with `coverage combine`

## Test Groups

### Unit Tests (`tests/unit/`)
Test individual functions through their public interfaces. Prefer testing private functionality indirectly (via the public API) rather than calling private methods directly. Keep tests fast and isolated.

### Integration Tests (`tests/integration/`)
End-to-end tests using actual HTML input files and expected output. Verify that the full linting/formatting pipeline works correctly on real-world scenarios.

### Private Tests (`tests/private/`)
Direct testing of private methods when the public interface doesn't provide adequate coverage. Use sparingly. The linter relaxes private-access rules here (but not in other test directories).

## Running Tests

**All tests + combined coverage**:
```bash
make test
```

**Individual groups (faster feedback)**:
```bash
make test-unit
make test-integration
make test-private
```

**Direct pytest** (for a specific file or test):
```bash
pytest tests/unit/test_linter.py -vv
pytest tests/unit/test_linter.py::TestClass::test_method -vv
```

## Coverage

- Combined coverage must be ≥ 91% or `make test` fails
- Use `coverage report -m` to see which lines are missing coverage
- Coverage source is always `cutesy/` (the main package)

## Notes to Add

- Test fixture patterns (how integration test HTML files are organized)
- Mock/stub conventions
- Common assertion patterns for linting results
- How to add a new integration test case
