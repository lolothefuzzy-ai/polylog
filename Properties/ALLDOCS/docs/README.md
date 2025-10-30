# Polylog Code Structure

## Overview

The codebase is organized into the following directory structure:

```
code/
├── __init__.py        # Main package initialization
├── gui/              # GUI components
│   ├── __init__.py
│   └── qt5/         # PyQt5-based GUI implementation
│       ├── app_qt5.py
│       ├── main_window_qt5.py
│       └── viewport_qt5.py
├── core/             # Core simulation components
│   ├── __init__.py
│   ├── managers.py
│   ├── canonical_system_integration.py
│   └── bvh3d.py
├── api/              # API and server components
│   ├── __init__.py
│   ├── server.py
│   └── security.py
└── utils/            # Utility functions and helpers
    └── __init__.py

```

## Components

### GUI (code/gui)
Contains all graphical user interface components, primarily using PyQt5.
- `qt5/`: PyQt5-specific implementations
  - `app_qt5.py`: Application entry point
  - `main_window_qt5.py`: Main application window
  - `viewport_qt5.py`: 3D OpenGL viewport

### Core (code/core)
Core simulation and processing logic.
- `managers.py`: Various manager classes for simulation components
- `canonical_system_integration.py`: System-wide integration
- `bvh3d.py`: 3D bounding volume hierarchy implementation

### API (code/api)
API server and security components.
- `server.py`: FastAPI server implementation
- `security.py`: API security layer

### Utils (code/utils)
Utility functions and helper classes used across the application.

## Usage

The main entry point remains `main.py` in the root directory, which provides different launch modes:
- GUI (default)
- API server
- Demo mode
- Combined mode

## ALLDOCS cleanup summary

During a recent cleanup I archived legacy and backup files and consolidated key documentation for easy access:

- Created `archive/backups` and `archive/legacy` at the repository root and moved detected backup and legacy folders there (no files were deleted).
- Created `docs/ALLDOCS_cleaned` and moved the most relevant files from `ALLDOCS` for quick access (for example `README.md`, `QUICK_START_TESTING.txt`, `stable_polyforms.jsonl`, `validators.py`, and `test_3d_integration.py`).
- Moved `ALLDOCS/_archive_legacy_code`, `ALLDOCS/_archive_legacy_docs`, `ALLDOCS/.github`, and large cache folders to `archive/legacy` to reduce noise in the top-level docs view.

If you want more files moved from `ALLDOCS` into `docs/ALLDOCS_cleaned`, or prefer different selection rules (e.g., keep all tests or only doc files), tell me the policy and I will apply it.