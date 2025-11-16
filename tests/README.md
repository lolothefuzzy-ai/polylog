# Tests

This directory contains all test files for the Polylog6 project.

## Structure

- `unit/` - Unit tests for individual components
- `integration/` - Integration tests across components
- `e2e/` - End-to-end tests for complete workflows
- `fixtures/` - Test data and fixtures
- `utils/` - Test utilities and helpers

## Running Tests

```bash
# Run all tests
python scripts/launcher.py test

# Run specific test types
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

## Test Data

Test fixtures are organized by component:
- `fixtures/polyhedra/` - Geometric test data
- `fixtures/images/` - Test images for detection
- `fixtures/api/` - API request/response examples