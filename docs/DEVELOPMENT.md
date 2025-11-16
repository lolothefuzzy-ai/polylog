# Development Guide

## Quick Start

```bash
# Start development environment
python scripts/unified_launcher.py dev

# Run tests
python scripts/unified_launcher.py test

# Build
python scripts/unified_launcher.py build
```

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

- `unified_launcher.py` - Main launcher
- `run_tests_in_workspace.py` - Test runner
- `organize_project.py` - Project organization

