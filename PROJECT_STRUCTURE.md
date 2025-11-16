# Polylog6 Project Structure

## Professional Desktop Application Structure

```
polylog6/
├── README.md                    # Main entry point
├── .cursorrules                 # Cursor IDE configuration
├── .gitignore                   # Git ignore rules
├── .github/                     # GitHub workflows & templates
│   ├── workflows/
│   │   ├── ci.yml              # CI/CD pipeline
│   │   └── storage-regression.yml
│   ├── dependabot.yml
│   └── .mergify.yml            # PR automation
├── src/                         # All source code
│   ├── polylog6/               # Python backend package
│   │   ├── api/                # FastAPI endpoints
│   │   ├── detection/          # Image detection
│   │   ├── simulation/         # Simulation engines
│   │   ├── storage/            # Storage layer
│   │   ├── monitoring/         # System monitoring
│   │   └── ...
│   ├── frontend/               # React/Babylon.js frontend
│   │   ├── src/
│   │   │   ├── components/     # React components
│   │   │   ├── services/       # API services
│   │   │   ├── tests/          # Test suites
│   │   │   └── ...
│   │   └── package.json
│   └── desktop/                # Tauri desktop app
│       └── src-tauri/          # Rust backend
├── tests/                       # All test files
│   ├── test_*.py               # Python tests
│   └── ...
├── scripts/                     # Utility scripts
│   ├── unified_launcher.py     # Main launcher
│   ├── auto_test.py            # Automated testing
│   └── ...
├── docs/                        # Documentation
│   ├── architecture/           # System architecture
│   ├── api/                     # API specs
│   └── archive/                # Historical docs
├── config/                      # Configuration files
├── data/                        # Static data
│   └── catalogs/               # Polyform catalogs
└── storage/                     # Runtime storage
```

## Key Features

- **Clean root**: Only essential files
- **Organized source**: All code in `src/`
- **Centralized tests**: All tests in `tests/`
- **Documentation**: Organized in `docs/`
- **Legacy archived**: Old files in `docs/archive/`

## Development Commands

```bash
python scripts/unified_launcher.py dev              # Start dev environment
python scripts/unified_launcher.py test:visual:workspace  # Visual tests in workspace
python scripts/unified_launcher.py test:auto       # Automated tests
```

