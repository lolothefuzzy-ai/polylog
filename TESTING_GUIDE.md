# Testing Guide for Polylog6

## Quick Start

### Run All Tests
```bash
python scripts/unified_launcher.py test:all
```

### Run Visual Tests (Browser Visible)
```bash
python scripts/unified_launcher.py test:headed
```

### Watch Mode (Auto-run on Changes)
```bash
python scripts/unified_launcher.py test:watch
```

### Interactive Test UI
```bash
python scripts/unified_launcher.py test:ui
```

## Test Types

### Backend Tests (Python)
- **Location**: `tests/`
- **Run**: `pytest tests/ -v`
- **Coverage**: Engine validation, API endpoints, storage, compression

### Frontend Tests (Playwright)
- **Visual Tests**: `src/frontend/tests/visual/`
  - Basic rendering
  - Interactive features (drag-drop, rotation, snapping)
  - Polyhedra library
  - Human interaction workflows

- **Integration Tests**: `src/frontend/tests/integration/`
  - Full system workflows
  - Generation pipeline
  - Unicode compression
  - API integration

- **Performance Tests**: `src/frontend/tests/performance/`
  - Benchmark tests
  - Architecture performance

## Running Tests in Workspace

### 1. Ensure Servers Are Running
```bash
# Start dev environment (API + Frontend)
python scripts/unified_launcher.py dev
```

### 2. Run Tests
```bash
# All tests
python scripts/run_tests_in_workspace.py

# Specific test type
python scripts/run_tests_in_workspace.py --type visual
python scripts/run_tests_in_workspace.py --type backend
python scripts/run_tests_in_workspace.py --type integration

# With visible browser
python scripts/run_tests_in_workspace.py --type visual --headed
```

### 3. Watch Mode
```bash
# Automatically runs tests when files change
python scripts/watch_tests.py

# Watch specific type
python scripts/watch_tests.py --type frontend
```

## Test Commands Reference

| Command | Description |
|---------|-------------|
| `test:all` | Run all tests (backend + frontend) |
| `test:visual` | Run visual rendering tests |
| `test:integration` | Run integration tests |
| `test:performance` | Run performance benchmarks |
| `test:watch` | Watch mode - auto-run on changes |
| `test:ui` | Open Playwright UI for interactive testing |
| `test:headed` | Run browser tests in visible mode |

## Writing New Tests

### Visual Test Example
```javascript
import { test, expect } from '@playwright/test';

test('My feature works', async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('.my-component');
  
  // Your test code
  await expect(page.locator('.my-component')).toBeVisible();
});
```

### Backend Test Example
```python
import pytest

def test_my_feature():
    # Your test code
    assert True
```

## Test Reports

- **HTML Report**: Generated in `src/frontend/playwright-report/`
- **Coverage**: Run `pytest --cov` for coverage reports
- **Traces**: Available in `test-results/` for failed tests

## Troubleshooting

### Tests Fail to Start
- Ensure servers are running: `python scripts/unified_launcher.py dev`
- Check ports: API (8000), Frontend (5173)
- Install dependencies: `npm install` in `src/frontend/`

### Browser Tests Don't Run
- Install Playwright browsers: `npx playwright install`
- Use `--headed` flag to see what's happening
- Check browser console in Playwright UI mode

### Watch Mode Not Working
- Ensure `watchdog` is installed: `pip install watchdog`
- Check file paths are correct
- Restart watch mode if needed

