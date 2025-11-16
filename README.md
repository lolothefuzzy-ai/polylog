# Polylog6

Polyform visualization and analysis system combining geometric computation, pattern discovery, and interactive visualization.

## Quick Start

```bash
# Start development
python scripts/unified_launcher.py dev

# Run all tests (backend-frontend integration)
python scripts/automated_test_suite.py --type all

# Quick visualization test
python scripts/test_visualization_quick.py
```

## Architecture

- **Backend**: Python FastAPI with unified geometry backend (Netlib integration)
- **Frontend**: React + Babylon.js for 3D visualization
- **Desktop**: Tauri (Rust) wrapper
- **Storage**: Tiered Unicode compression system (Series A/B/C/D)

## Key Features

- Interactive polygon workspace
- Tier 0 encoding (Series A/B/C/D)
- Tier 1 solid generation (Platonic, Archimedean, Johnson)
- GPU warming and optimization
- Atomic chain detection
- Unified backend geometry system

## Testing

All tests focus on backend-frontend integration:

```bash
# Run all tests
python scripts/automated_test_suite.py --type all

# Backend stability tests
python scripts/automated_test_suite.py --type backend-stability

# Backend-frontend integration tests
python scripts/automated_test_suite.py --type frontend-integration

# Or use npm scripts
npm test
npm run test:backend
npm run test:integration
```

## Development

See `docs/DEVELOPMENT.md` for development guide.

## Documentation

- `docs/ARCHITECTURE.md` - System architecture
- `docs/WORKSPACE_INTERACTION_ARCHITECTURE.md` - Interaction model
- `docs/DEVELOPMENT.md` - Development guide

## License

[Your License Here]
