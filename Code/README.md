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