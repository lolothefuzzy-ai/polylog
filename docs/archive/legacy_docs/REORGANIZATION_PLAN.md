# Polylog6 Professional Folder Structure

## Target Organization

```
polylog6/
├── README.md                          # Main project entry point
├── LICENSE                            # Project license
├── .gitignore                         # Git ignore rules
├── .github/                           # GitHub workflows & templates
│   └── workflows/
│       ├── ci.yml                    # Continuous integration
│       └── release.yml               # Release automation
├── docs/                             # All documentation
│   ├── README.md                     # Documentation index
│   ├── architecture/                  # System architecture docs
│   │   ├── POLYLOG6_ARCHITECTURE.md  # Main architecture
│   │   └── components/               # Component-specific docs
│   ├── api/                          # API documentation
│   │   └── openapi_schema.yaml
│   ├── guides/                       # User and developer guides
│   │   ├── getting-started.md
│   │   ├── development.md
│   │   └── deployment.md
│   └── archive/                      # Historical/obsolete docs
├── src/                              # All source code
│   ├── README.md                     # Source code overview
│   ├── polylog6/                     # Main Python package
│   │   ├── __init__.py
│   │   ├── api/                      # API layer
│   │   ├── core/                     # Core business logic
│   │   ├── detection/                # Image detection module
│   │   ├── discovery/                # Pattern discovery module
│   │   ├── storage/                  # Data storage layer
│   │   ├── simulation/               # Simulation engine
│   │   └── combinatorial/            # Combinatorial calculations
│   ├── frontend/                     # Frontend application
│   │   ├── src/                      # Frontend source
│   │   ├── public/                   # Static assets
│   │   ├── package.json
│   │   └── vite.config.js
│   ├── desktop/                      # Tauri desktop app
│   │   ├── src-tauri/                # Rust backend
│   │   └── build.rs
│   └── shared/                       # Shared utilities
│       ├── types/                    # TypeScript types
│       └── schemas/                  # JSON schemas
├── tests/                            # All test files
│   ├── README.md                     # Testing overview
│   ├── unit/                         # Unit tests
│   ├── integration/                  # Integration tests
│   ├── e2e/                          # End-to-end tests
│   ├── fixtures/                     # Test data
│   └── utils/                        # Test utilities
├── scripts/                          # Utility scripts
│   ├── launcher.py                   # Unified launcher
│   ├── build/                        # Build scripts
│   ├── deploy/                       # Deployment scripts
│   └── maintenance/                  # Maintenance scripts
├── config/                           # Configuration files
│   ├── monitoring.yaml
│   ├── segmentation_config.yaml
│   └── environments/                 # Environment-specific configs
│       ├── development.yaml
│       ├── staging.yaml
│       └── production.yaml
├── data/                             # Static data files
│   ├── polyhedra/                     # Polyhedra definitions
│   ├── catalogs/                     # Geometry catalogs
│   └── fixtures/                     # Test fixtures
├── tools/                            # Development tools
│   ├── data_generation/              # Data generation tools
│   └── benchmarking/                 # Performance tools
├── requirements/                     # Dependencies
│   ├── base.txt                      # Base Python dependencies
│   ├── dev.txt                       # Development dependencies
│   └── conda.yaml                    # Conda environment
└── storage/                          # Runtime storage
    ├── chunks/                       # Data chunks
    └── cache/                        # Cache files
```

## Key Principles

1. **Clear Separation of Concerns**
   - Source code in `src/`
   - Tests in `tests/`
   - Documentation in `docs/`
   - Configuration in `config/`

2. **Logical Grouping**
   - Frontend, backend, and shared code clearly separated
   - Tests organized by type (unit, integration, e2e)
   - Documentation organized by purpose

3. **Consistent Naming**
   - Use lowercase with underscores for directories
   - Use descriptive names
   - Keep depth reasonable (max 4 levels)

4. **No Build Artifacts in Repo**
   - Virtual environments excluded
   - Build outputs in `storage/` or `.gitignore`
   - Cache files excluded

5. **Clear Entry Points**
   - README files in major directories
   - Main launcher in `scripts/`
   - Package files at appropriate levels