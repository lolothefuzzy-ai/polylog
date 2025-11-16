# Polylog6 Project Structure

## Directory Layout

```
polylog6/
├── src/                    # Source code
│   ├── polylog6/          # Backend Python package
│   ├── frontend/          # React frontend
│   └── desktop/           # Tauri desktop app
├── tests/                 # Test files
├── scripts/               # Development scripts
│   ├── unified_launcher.py
│   ├── run_tests_in_workspace.py
│   ├── organize_project.py
│   └── final_cleanup.py
├── docs/                  # Essential documentation
│   ├── ARCHITECTURE.md
│   ├── DEVELOPMENT.md
│   └── WORKSPACE_INTERACTION_ARCHITECTURE.md
├── data/                  # Data catalogs
│   └── catalogs/
├── .github/              # GitHub Actions workflows
│   └── workflows/
├── .vscode/              # VS Code/Cursor settings
│   ├── settings.json
│   ├── extensions.json
│   ├── tasks.json
│   └── launch.json
├── README.md             # Main README
├── requirements.txt       # Python dependencies
└── package.json          # Root package.json
```

## Key Files

### Scripts
- `unified_launcher.py` - Main development launcher
- `run_tests_in_workspace.py` - Test runner
- `organize_project.py` - Project organization
- `final_cleanup.py` - Cleanup utility
- `verify_integration.py` - Integration verification

### Configuration
- `.vscode/settings.json` - Editor settings
- `.vscode/extensions.json` - Recommended extensions
- `.vscode/tasks.json` - Build tasks
- `.vscode/launch.json` - Debug configurations
- `.github/workflows/ci.yml` - CI/CD pipeline

### Documentation
- `README.md` - Quick start
- `docs/ARCHITECTURE.md` - System architecture
- `docs/DEVELOPMENT.md` - Development guide
- `docs/WORKSPACE_INTERACTION_ARCHITECTURE.md` - Interaction model

## Development

See `docs/DEVELOPMENT.md` for development workflow.
