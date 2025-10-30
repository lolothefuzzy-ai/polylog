# Polylog Simulator v0.2.0

**Interactive Polyform Design & Exploration System**

> **NEW in v0.2:** Unified generator system, 3D collision detection, integrated bonding system

## 🚀 Start Here

```bash
python main.py
```

That's it! See `python main.py -h` for options.

## 📖 Documentation

All guides are in [DOCS.md](DOCS.md):
- Getting started
- System architecture  
- API reference
- Troubleshooting

## 🎯 Three Modes

```bash
python main.py              # Combined: API + Demo (default)
python main.py api          # API server only
python main.py demo         # Interactive demo only
```

## 📂 Quick Links

- **Getting started?** → [QUICK_START.md](QUICK_START.md)
- **Understanding design?** → [ENTRY_POINT_CLARIFICATION.md](ENTRY_POINT_CLARIFICATION.md)
- **System architecture?** → [ENTRY_POINT_ARCHITECTURE.md](ENTRY_POINT_ARCHITECTURE.md)
- **Implementation details?** → [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Integration status?** → [INTEGRATION_STATUS.md](INTEGRATION_STATUS.md)
- **Need help?** → [DOCS.md](DOCS.md)

```
╔═══════════════════════════════════════════════════════════╗
║           POLYLOG SIMULATOR - Starting                  ║
║         Interactive Polyform Design System              ║
╚═══════════════════════════════════════════════════════════╝

Mode: INTERACTIVE DEMO
Running Polylog library integration demo...

╔══════════════════════════════════════════════════════════╗
║                                                          ║
║          POLYLOG LIBRARY INTEGRATION DEMO                ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

Then you'll see a **live demonstration** that:

1. **Generates random polygon assemblies** - Creates 5-15 polygons in different layouts:
   - Circular arrangement
   - Grid layout
   - Spiral pattern
   - Random clusters
   - Linear arrays
   - Organic placement

2. **Renders visual thumbnails** - Creates PNG images of each polygon and saves them

3. **Stores in a library** - Saves everything to a searchable database

4. **Simulates drag-and-drop** - Shows how you'd move polygons around in a GUI

## What This Program Does

**Polylog is a research tool for designing and analyzing 2D/3D polygon assemblies.**

Think of it as:
- A CAD tool for regular polygons (triangles, squares, pentagons, etc.)
- A combinatorial explorer that calculates how many ways shapes can fold
- A visual library system for managing polygon designs
- An intelligent placement engine that knows geometric constraints

### Core Capabilities

#### 1. **Random Assembly Generation**
```
Generates 6 assembly patterns with various polygon types:
- Triangles through 12-sided polygons
- Adaptive learning (learns which types work best)
- Smart spatial placement
- Full 3D mesh support
```

#### 2. **Visual Library System**
```
- Saves polygon designs to persistent storage
- Renders color-coded thumbnails (red=triangles, blue=squares, etc.)
- Search by properties (sides, type, etc.)
- Manages complete assemblies
```

#### 3. **Drag-and-Drop Interface** (Framework-ready)
```
- Snap-to-grid placement
- Visual ghost preview during drag
- Multi-select support
- Event-driven callbacks
```

#### 4. **Combinatorial Analysis**
```
- Calculates complexity estimates (N values)
- Tracks convergence over time
- Shows confidence intervals
- Monitors stability
```

## What Would It Look Like to Someone Who Doesn't Know?

If you just ran this without context, you'd see:

### Terminal Output
```
Generating circular assembly...
  Generated 8 polyforms
  Types: {3: 2, 4: 3, 5: 1, 6: 2}

Generating grid assembly...
  Generated 8 polyforms
  Types: {3: 1, 4: 4, 5: 2, 6: 1}

[... continues through 6 patterns ...]

Rendering 5 individual polyform thumbnails...
  Saved 4-gon thumbnail: demo_thumbnails/polyform_0.png
  Saved 5-gon thumbnail: demo_thumbnails/polyform_1.png
  Saved 3-gon thumbnail: demo_thumbnails/polyform_2.png
  [...]

Adding 5 polyforms to library...
  Added 4-gon with ID: a3b7c9d1...
  Added 5-gon with ID: e4f8a2b6...
  [...]

Simulating drag-drop of 5 polyforms...
  [1] Started drag for polyform a3b7c9d1...
      Dragging to (150.0, 150.0)...
      ✓ Dropped at (0.0, 0.0)
  [...]

ALL DEMOS COMPLETED SUCCESSFULLY!

Generated files:
  - demo_thumbnails/       (thumbnail images)
  - demo_library/          (library database)
```

### Generated Files

**demo_thumbnails/**
- `polyform_0.png` - Blue square thumbnail
- `polyform_1.png` - Green pentagon thumbnail
- `polyform_2.png` - Red triangle thumbnail
- `polyform_3.png` - Orange hexagon thumbnail
- `polyform_4.png` - Purple heptagon thumbnail
- `assembly_complete.png` - All shapes together

**demo_library/**
- `polyforms.json` - Database of individual polygons
- `assemblies.json` - Complete assembly designs

## What This Is Actually For

### Research Applications
- **Polyform geometry** - Study how regular polygons fold and connect
- **Combinatorial analysis** - Calculate state spaces for polygon assemblies
- **Automated design** - Generate valid polygon configurations
- **Constraint solving** - Find arrangements that satisfy geometric rules

### Practical Use Cases
- Design origami-like folding patterns
- Explore tiling and tessellation
- Generate 3D models from 2D polygon nets
- Analyze convergence of geometric parameters
- Build polygon-based computational models

## Quick Start

### Run the Demo
```bash
python main.py
```

That's it! You'll see the 4-part demonstration.

### Modes Available
```bash
python main.py demo    # Interactive demo (default)
python main.py api     # Launch REST API server
```

### Requirements
- Python 3.8+
- numpy
- Pillow (PIL)

```bash
pip install numpy pillow
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│  POLYLOG - Polygon Assembly Design System           │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  Random Assembly Generator                 │    │
│  │  - 6 spatial layout patterns               │    │
│  │  - Adaptive type selection                 │    │
│  │  - 3D mesh generation                      │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  Library System                            │    │
│  │  - Persistent JSON storage                 │    │
│  │  - Visual thumbnails (auto-colored)        │    │
│  │  - Search & retrieval                      │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  Drag-Drop Handler                         │    │
│  │  - Snap-to-grid placement                  │    │
│  │  - Multi-select support                    │    │
│  │  - Framework-agnostic                      │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  Analysis Tools                            │    │
│  │  - Combinatorial estimates                 │    │
│  │  - Convergence tracking                    │    │
│  │  - Stability metrics                       │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Key Concepts

### Polyform
A 2D polygon (3-12 sides) that can exist in 3D space and connect to other polyforms.

### Assembly
A collection of polyforms that may be connected together through shared edges.

### Library
A persistent storage system that saves polyforms and assemblies with visual thumbnails.

### Pattern
A spatial layout strategy (circular, grid, spiral, etc.) used when generating assemblies.

### Thumbnail
A visual representation (PNG image) of a polyform, color-coded by polygon type.

## File Structure

```
Polylog6/
├── main.py                           # Entry point
├── random_assembly_generator.py      # Generates random assemblies
├── library_thumbnail_renderer.py     # Creates visual thumbnails
├── library_drag_drop.py              # Drag-drop interaction handler
├── polyform_library.py               # Library management
├── demo_library_integration.py       # Integration demo
├── polygon_utils.py                  # Polygon creation utilities
├── managers.py                       # Workspace/assembly managers
├── cleanup.py                        # Cleanup utility
├── LIBRARY_INTEGRATION.md            # Technical documentation
└── README.md                         # This file
```

## What's Next?

The current system demonstrates:
- ✅ Random polygon generation with learning
- ✅ Visual thumbnail rendering
- ✅ Persistent library storage
- ✅ Drag-drop simulation
- ✅ Snap-to-grid placement

**Planned enhancements:**
- 🔄 Full GUI application (desktop_app.py)
- 🔄 Interactive 3D viewport
- 🔄 Real-time editing
- 🔄 Visual convergence displays

## Documentation

- **LIBRARY_INTEGRATION.md** - Technical details on the three new modules
- **GETTING_STARTED.md** - Quick introduction to the system
- **README_UNIFIED.md** - Complete documentation index (127 docs!)

## Status

**Current:** Demo-ready, library system complete  
**Next Step:** GUI integration with Qt/PySide6  
**Long-term:** Full interactive design environment

## Questions?

### "What exactly am I looking at?"
A research tool for designing and analyzing polygon assemblies, currently demonstrating its library system through an automated demo.

### "Can I use this to design something?"
Yes! The library system lets you save and organize polygon designs. The GUI for interactive design is in development.

### "What's with all the numbers and types?"
The system tracks combinatorial complexity (how many ways shapes can arrange) and uses polygon types (3-gon = triangle, 4-gon = square, etc.).

### "Why random generation?"
It's one way to explore the design space. You can also create specific designs manually (API available, GUI coming).

---

**Polylog** - Where polygons meet computation and design  
*A research tool for exploring geometric assemblies*
