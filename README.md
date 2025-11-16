# Polylog6

Polyform visualization and analysis system combining geometric computation, pattern discovery, and interactive visualization.

## Quick Start

```bash
# Start development
python scripts/unified_launcher.py dev

# Run tests
python scripts/unified_launcher.py test

# Build
python scripts/unified_launcher.py build
```

## Architecture

- **Backend**: Python FastAPI with CGAL integration
- **Frontend**: React + Babylon.js for 3D visualization
- **Desktop**: Tauri (Rust) wrapper
- **Storage**: Tiered Unicode compression system

## Key Features

- Interactive polygon workspace
- Tier 0 encoding (Series A/B/C/D)
- Tier 1 solid generation (Platonic, Archimedean, Johnson)
- GPU warming and optimization
- Atomic chain detection
- Unified backend geometry system

## Development

See `docs/DEVELOPMENT.md` for development guide.

## Documentation

- `docs/ARCHITECTURE.md` - System architecture
- `docs/WORKSPACE_INTERACTION_ARCHITECTURE.md` - Interaction model
- `docs/DEVELOPMENT.md` - Development guide

## Testing

```bash
# Python tests
pytest tests/

# Frontend tests
cd src/frontend && npm test

# Integration tests
python scripts/run_tests_in_workspace.py
```

## License

[Your License Here]
