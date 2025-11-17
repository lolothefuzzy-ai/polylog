# Polylog6

Polyform visualization and analysis system combining geometric computation, pattern discovery, and interactive visualization.

## Quick Start

```bash
# Start development
python scripts/dev.py

# Run all tests (backend-frontend integration)
python scripts/test.py

# Build for production
python scripts/build.py
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
python scripts/test.py

# Or use npm scripts
npm test
npm run test:backend
npm run test:integration
```

## Development

See `docs/ARCHITECTURE.md` for architecture and development guide.

## Documentation

- `docs/ARCHITECTURE.md` - **Single source of truth** (architecture, code references, Track A/B)

## License

[Your License Here]
