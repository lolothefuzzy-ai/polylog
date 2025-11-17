# Development Guide

## Quick Start

```bash
# Start unified interactive development (recommended)
# This launches API + Frontend with integrated testing support
python scripts/unified_interactive_dev.py

# Or use unified launcher
python scripts/unified_launcher.py dev

# Run tests
python scripts/unified_launcher.py test

# Build
python scripts/unified_launcher.py build
```

### Unified Interactive Development Service

The `unified_interactive_dev.py` script provides a complete development environment:

```bash
# Start dev environment (API + Frontend)
python scripts/unified_interactive_dev.py

# Start dev + run interactive tests
python scripts/unified_interactive_dev.py --test

# Start API only
python scripts/unified_interactive_dev.py --api-only

# Start frontend only
python scripts/unified_interactive_dev.py --frontend-only
```

**Features**:

- Automatically starts API server (port 8000) and Frontend dev server (port 5173)
- Waits for servers to be ready before proceeding
- Optional interactive Playwright tests
- Clean shutdown of all processes on Ctrl+C
- Tracks user interactions during development

## Project Structure

```
polylog6/
├── src/
│   ├── polylog6/          # Backend Python
│   ├── frontend/          # React frontend
│   └── desktop/           # Tauri desktop
├── tests/                 # Test files
├── scripts/               # Development scripts
├── docs/                  # Documentation
└── data/                  # Data catalogs
```

## Development Workflow

1. **Make Changes** - Edit code
2. **Test** - Run tests
3. **Commit** - Use conventional commits
4. **Push** - Sync to GitHub
5. **CI/CD** - GitHub Actions runs automatically

## Testing

```bash
# Python tests
pytest tests/

# Frontend tests
cd src/frontend && npm test

# Integration tests
python scripts/run_tests_in_workspace.py
```

## Code Style

- **Python**: PEP 8, type hints, ruff linting
- **TypeScript**: Strict mode, ESLint
- **Rust**: rustfmt conventions

## Key Scripts

- `unified_interactive_dev.py` - **Unified interactive development service** (recommended)
- `unified_launcher.py` - Main launcher
- `automated_test_suite.py` - Automated test suite
- `run_tests_in_workspace.py` - Test runner
- `organize_project.py` - Project organization
