# Polylog6 Unified Launcher

The `launcher.py` script provides a unified interface for all development, build, and deployment tasks.

## Installation

First, ensure you have Python 3.11+, Node.js, and Rust/Cargo installed.

Then run:
```bash
python launcher.py install
```

## Usage

### Development Commands

```bash
# Start full development environment (API + Frontend)
python launcher.py dev

# Start individual components
python launcher.py dev:frontend    # Frontend dev server
python launcher.py dev:api         # API server
python launcher.py dev:tauri       # Tauri desktop app
```

### Build Commands

```bash
# Build complete application
python launcher.py build

# Build individual components
python launcher.py build:frontend  # Frontend production build
python launcher.py build:tauri     # Tauri backend build
```

### Utility Commands

```bash
python launcher.py install         # Install all dependencies
python launcher.py test           # Run all tests
python launcher.py clean          # Clean build artifacts
```

## Windows Users

For convenience on Windows, you can use the `launch.bat` wrapper:
```batch
launch.bat dev
launch.bat build
```

## What This Replaced

This unified launcher replaces the following duplicate/obsolete files:
- `build.ps1` → `python launcher.py build`
- `start.bat` → `python launcher.py dev`
- `launch_api.bat` → `python launcher.py dev:api`
- `launch_gui.bat` → `python launcher.py dev:tauri`
- `build_installer.bat` → `python launcher.py build`
- `install_dependencies.bat` → `python launcher.py install`

## Project Structure

The launcher assumes the following structure:
```
Polylog6/
├── src-tauri/           # Tauri/Rust backend
├── package.json         # Frontend dependencies
├── requirements.txt     # Python dependencies
├── launcher.py          # This script
└── PolylogCore/         # Legacy Python code
```