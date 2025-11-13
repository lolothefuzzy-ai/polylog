# Legacy UI Reference

This document captures the useful interaction patterns and layout notes from the retired legacy workspace.

## Application Shell

- **Main Menu**: top-left dropdown providing quick access to simulation modes and data import routines.
- **Dock Layout**: left sidebar lists tier selectors (Tier0–Tier3), right sidebar shows telemetry graphs.
- **Bottom Status Bar**: displays active geometry, last checkpoint timestamp, and ingestion pipeline state.

## Panels

- **Geometry Viewport**: center OpenGL panel embedded via PyQt5, supports rotation/zoom with mouse drag + wheel.
- **Catalog Browser**: tree view allowing drilldown by polygon edge count and series pair.
- **Telemetry Dashboard**: tabbed interface for alert feed, compression metrics, and dispatcher latency charts.
- **Control Palette**: floating palette hosting play/pause, checkpoint, and tier promotion buttons.

## Workflow Notes

- GUI entry point historically lived in `app_qt5.py` and `main_window_qt5.py`.
- Core simulation managers arranged under `core/managers.py` with optional BVH acceleration (`bvh3d.py`).
- API server toggle exposed from GUI menu; mapped to legacy FastAPI server module.

> For full legacy artifacts (PyQt5 sources, scripts, legacy API), consult the detached backup outside this repository.
