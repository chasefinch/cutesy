# Cutesy Development Guide

## Testing Strategy

Cutesy has three types of tests:

### Test Categories

#### Unit Tests (`tests/unit/`)
Test individual functions through their public interfaces. Generally prefer testing private functionality indirectly rather than calling private methods directly.

#### Integration Tests (`tests/integration/`)
End-to-end testing with actual HTML files and expected results. Make sure the system works as a whole with real-world scenarios.

#### Private Tests (`tests/private/`)
Direct testing of private methods when public interface testing isn't enough. Use sparingly - only when unit tests don't provide adequate coverage.

### Running Tests

- `make test-unit` - Run only unit tests
- `make test-integration` - Run only integration tests
- `make test-private` - Run only private tests
- `make test` - Run all tests with combined coverage

Each test type generates its own coverage data file, then `make test` combines them all.

### Linting Setup

The linter allows private member access in `tests/private/` but not elsewhere. This lets us test internal functionality when needed while keeping the main code clean.
