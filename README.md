# Polylog Polyform Visualizer

An interactive web-based visualization tool for the Polylog AKAD polyform generator, demonstrating the core principles of non-deformable equilateral polygon assembly.

## Overview

This visualizer implements the fundamental concepts from the Polylog6 architecture:

- **Non-deformable Polygons**: All polygons (3-20 sided) maintain perfect equilateral geometry
- **Unit Edge Length**: Every polygon edge has identical length (1.0 units) - no stretching or compression
- **Edge-to-Edge Attachment**: Polygons connect seamlessly without gaps or overlaps
- **Geometric Precision**: Internal angles and edge alignment follow strict mathematical rules

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
- Edge snapping utilities (implemented in `edgeSnapping.ts`)
- Attachment validation system
- Maintains geometric integrity across all operations

## Architecture Alignment

This visualizer aligns with the Polylog6 system architecture:

### Core Principles
1. **Equilateral Constraint**: Individual polygons are equilateral (not the overall polyform)
2. **Non-Deformable**: Shapes never stretch, bend, or deform
3. **Unit Edge**: All edges maintain identical length
4. **Gap-Free Assembly**: Only valid attachments (3-20 sided polygons can fill any gap)

### Technical Implementation
- **Polygon Geometry** (`lib/polygonGeometry.ts`): Generates perfect regular polygons
- **Edge Snapping** (`lib/edgeSnapping.ts`): Validates edge-to-edge connections
- **Visual Rendering**: SVG-based for precision and scalability
- **State Management**: React hooks for interactive manipulation

## Usage

### Basic Workflow
1. **Select** a polygon from the left palette (3-20 sides)
2. **Place** polygons by clicking on the canvas
3. **Move** polygons by clicking and dragging
4. **Rotate** selected polygons using the toolbar
5. **Delete** unwanted polygons with the delete button
6. **Clear All** to reset the workspace

### Keyboard Shortcuts
- Click polygon: Select/deselect
- Click canvas: Place selected polygon type
- Drag: Move polygon

## Design System

### Color Palette
- **Primary**: Indigo (#6366f1) - Main polygon color
- **Secondary**: Purple (#8b5cf6) - Selected state
- **Grid**: Subtle indigo overlay
- **Background**: Clean light theme

### Typography
- **Font**: Inter (Google Fonts)
- **Headings**: Bold, clear hierarchy
- **Body**: Clean, readable sans-serif

## Technical Stack

- **React 19**: Modern UI framework
- **TypeScript**: Type-safe development
- **Tailwind CSS 4**: Utility-first styling
- **shadcn/ui**: Component library
- **Vite**: Fast build tooling

## Future Enhancements

### Planned Features
- [ ] 3D visualization with THREE.js
- [ ] Polyhedra library (97 known polyhedra)
- [ ] Advanced edge snapping with visual guides
- [ ] Pattern recognition and validation
- [ ] Export to Polylog6 format
- [ ] Undo/redo functionality
- [ ] Keyboard shortcuts for rotation
- [ ] Snap-to-grid alignment
- [ ] Multi-select operations

### Backend Integration
- [ ] Connect to Polylog6 detection system
- [ ] Real-time pattern validation
- [ ] Compression metrics visualization
- [ ] Storage integration for saving patterns

## Development

### Prerequisites
- Node.js 18+
- pnpm

### Installation
```bash
# Install dependencies
pnpm install

# Run development server
pnpm dev

# Build for production
pnpm build
```

### Project Structure
```
client/
  src/
    components/
      PolygonPalette.tsx    # Polygon selection UI
      Canvas3D.tsx          # 3D canvas wrapper (future)
      Workspace.tsx         # 3D workspace (future)
    lib/
      polygonGeometry.ts    # Polygon math utilities
      edgeSnapping.ts       # Edge attachment logic
    pages/
      Home.tsx              # Main application
```

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

## References

- **Polylog6 Architecture**: Core system documentation
- **AKAD Polyform Generator**: Pattern generation algorithms
- **Equilateral Polygon Theory**: Geometric foundations

## License

Part of the Polylog6 project.

---

**Last Updated**: November 15, 2025
