# Polylog6

A sophisticated polyform visualization and analysis system that combines geometric computation, pattern discovery, and interactive visualization.

## Overview

Polylog6 is a comprehensive system for working with equilateral polyforms, featuring:

- **Non-deformable Polygons**: All polygons (3-20 sided) maintain perfect equilateral geometry
- **Unit Edge Length**: Every polygon edge has identical length (1.0 units) - no stretching or compression
- **Edge-to-Edge Attachment**: Polygons connect seamlessly without gaps or overlaps
- **Geometric Precision**: Internal angles and edge alignment follow strict mathematical rules
- **Interactive Visualization**: Web-based and desktop applications for exploring polyforms
- **Pattern Discovery**: Automated detection and analysis of polyform patterns

## Quick Start

```bash
# Install dependencies
python scripts/unified_launcher.py install

# Start development environment with visual testing
python scripts/unified_launcher.py desktop

# Run tests
python scripts/unified_launcher.py test

# Performance benchmarks
python scripts/unified_launcher.py benchmark
```

### Optimization & Continuous Testing

For novel systems development, we emphasize continuous visual testing and full system integration:

- **Visual Testing**: `python scripts/unified_launcher.py test:visual`
- **Integration Tests**: `python scripts/unified_launcher.py test:integration`
- **Performance**: `python scripts/unified_launcher.py benchmark`
- **Monitoring**: `python scripts/unified_launcher.py monitor`

See `QUICK_START_OPTIMIZATION.md` for quick reference and `DEVELOPMENT_WORKFLOW.md` for complete guide.

## Project Structure

- `src/` - All source code
  - `polylog6/` - Main Python package
  - `frontend/` - React/Babylon.js frontend
  - `desktop/` - Tauri desktop application
  - `shared/` - Shared types and schemas
- `tests/` - All test files
- `docs/` - Documentation
- `scripts/` - Utility scripts
- `config/` - Configuration files
- `data/` - Static data files
- `catalogs/` - Polyform catalogs and metadata

## Features

### Polygon Library
- 18 primitive polygons (Triangle through Icosagon)
- Visual preview of each polygon type
- Color-coded selection system
- Perfect equilateral geometry for all shapes

### Interactive Workspace
- **Click to Place**: Select a polygon and click to place it on the canvas
- **Drag to Move**: Click and drag placed polygons to reposition them
- **Rotate**: Select a polygon and use the rotate button (30° increments)
- **Delete**: Remove selected polygons
- **Visual Feedback**: Selected polygons show vertex indicators

### Geometric Validation
- Unit edge length calculation for each polygon type
- Edge snapping utilities
- Attachment validation system
- Maintains geometric integrity across all operations

## Architecture Alignment

### Core Principles
1. **Equilateral Constraint**: Individual polygons are equilateral (not the overall polyform)
2. **Non-Deformable**: Shapes never stretch, bend, or deform
3. **Unit Edge**: All edges maintain identical length
4. **Gap-Free Assembly**: Only valid attachments (3-20 sided polygons can fill any gap)

### Technical Implementation
- **Polygon Geometry**: Generates perfect regular polygons
- **Edge Snapping**: Validates edge-to-edge connections
- **Visual Rendering**: SVG and 3D rendering for precision and scalability
- **State Management**: React hooks for interactive manipulation

## Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- Rust (for desktop app)
- pnpm (recommended) or npm

### Installation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd src/frontend
npm install

# Install desktop dependencies (if building desktop app)
cd src/desktop/src-tauri
cargo build
```

### Running Tests
```bash
# Python tests
pytest

# Frontend tests
cd src/frontend
npm test

# Desktop tests
cd src/desktop/src-tauri
cargo test
```

## Documentation

- [Architecture Overview](documentation/POLYLOG6_README.md)
- [Getting Started Guide](INSTALL.md)
- [API Documentation](src/polylog6/api/openapi_schema.yaml)

## CI/CD

This project uses GitHub Actions for continuous integration:

- **Python Tests**: Automated testing with coverage reporting via Codecov
- **Frontend Tests**: Node.js tests and build verification
- **Desktop Tests**: Rust/Tauri build and test verification
- **Integration Tests**: End-to-end testing of the full system
- **Automated Merging**: Mergify handles PR merging and branch management

### Required GitHub Secrets
- `CODECOV_TOKEN` - For coverage reporting
- `SLACK_WEBHOOK_URL` - For notifications (optional)

## Mathematical Foundation

### Edge Length Calculation
For a regular polygon with `n` sides and circumradius `r`:
```
edge_length = 2 * r * sin(π / n)
```

### Radius for Unit Edge
To achieve unit edge length (1.0):
```
r = 1 / (2 * sin(π / n))
```

### Vertex Positions
For polygon centered at `(cx, cy)` with rotation `θ`:
```
vertex_i = (
  cx + r * cos(θ + 2πi/n),
  cy + r * sin(θ + 2πi/n)
)
```

## License

Part of the Polylog6 project.

---

**Last Updated**: November 15, 2025
