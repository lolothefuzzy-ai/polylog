# Workspace Interaction Architecture

## Overview

This document defines the interaction model for Polylog6 workspace based on unit edges, internal angles, and chain/subform movement patterns similar to Blender, Rhino, and SketchUp.

## Core Principles

### 1. Unit Edge Length
- **All edges = 1.0 unit** across entire workspace
- Polygons defined by **series of unit edges** and **internal angles**
- Scaling achieved through polygon count, not edge length
- Visualization optimized for unit edge representation

### 2. Polygon Representation

**CRITICAL**: Primitives are NOT Tier 0. Tier 0 deals with polygon-to-polygon attachments.

- **Primitives**: 3-20 sided polygons (separate structure, not Tier 0)
- **Tier 0**: Polygon-to-polygon attachment sequences (Series A/B/C/D + subscript)
- **Series Structure** (canonical from `tier0_generator.py`):
  - **Series A**: [3, 4, 5, 6, 7, 8, 9, 10, 11] - positions 1-9
  - **Series B**: [20, 4, 6, 8, 10, 12, 14, 16, 18] - positions 1-9 (complementary to A)
  - **Series C**: [3, 6, 9, 12, 15, 18, 8, 7, 10] - positions 1-9 (multiples of 3 + variations)
  - **Series D**: [14, 20, 13, 11, 4, 16, 17, 5, 19] - positions 1-9 (complementary set)

**Primitive Definition**:
- Defined by: `{sides, unit_edge_length: 1.0, internal_angle: (n-2)*180/n}`
- Circumradius calculated: `R = 1.0 / (2 * sin(π/n))`
- All polygons start flat on XY plane (z=0)

### 3. Internal Angles
- Triangle: 60° (internal), 120° (external)
- Square: 90° (internal), 90° (external)
- Pentagon: 108° (internal), 72° (external)
- Hexagon: 120° (internal), 60° (external)
- Formula: `internal_angle = (n-2) * 180 / n`

## Interaction Workflow

### Phase 1: Polygon Instantiation
**Method**: Button-based (NOT drag-drop)
- User selects polygon from slider (A-R)
- Clicks "Add to Workspace" button
- Polygon appears in workspace at default position
- All edges start as **open** (available for attachment)

### Phase 2: Individual Polygon Movement
**Method**: Click-and-drag within workspace
- Click polygon to select
- Drag to move freely in workspace
- **Rotation**: Hold Shift while dragging
- Visual feedback: Highlight selected polygon
- Snap guides appear when near other polygons

### Phase 3: Edge Attachment
**Method**: Automatic snapping when edges align
- Move polygon near another polygon
- System detects edge proximity (< threshold)
- Visual feedback: Green snap guides on compatible edges
- Drop to attach: Edges snap edge-to-edge
- Fold angle applied based on polygon types
- Attached edges marked as **closed**

### Phase 4: Chain/Subform Movement
**Method**: Move attached groups as units
- Once polygons are attached, they form a **chain** or **subform**
- Click any polygon in chain to select entire chain
- Drag to move entire chain/subform together
- All attachments preserved during movement
- Relative positions maintained

## Implementation Details

### Button-Based Instantiation

```javascript
// PolygonSlider.jsx
handleAdd() {
  const polygon = polygons[selectedIndex];
  // Emit event to add polygon to workspace
  onSelect(polygon);
}

// BabylonScene.jsx
useEffect(() => {
  // When new polygon selected, instantiate in workspace
  if (selectedPolyhedra.length > workspacePolygons.length) {
    const newPolygon = selectedPolyhedra[selectedPolyhedra.length - 1];
    addPolygonToWorkspace(newPolygon);
  }
}, [selectedPolyhedra]);
```

### Workspace Polygon State

```javascript
class WorkspacePolygon {
  id: string;
  symbol: string;  // A-R
  sides: number;
  mesh: BABYLON.Mesh;
  position: Vector3;
  rotation: Quaternion;
  openEdges: Set<number>;  // Edge indices still open
  attachedTo: Map<number, Attachment>;  // edgeIndex -> attachment info
  chainId: string | null;  // If part of chain/subform
}
```

### Chain/Subform Detection

```javascript
class ChainManager {
  chains: Map<string, Chain>;
  
  detectChain(polygonId: string): Chain {
    // BFS to find all connected polygons
    const visited = new Set();
    const chain = [];
    const queue = [polygonId];
    
    while (queue.length > 0) {
      const current = queue.shift();
      if (visited.has(current)) continue;
      visited.add(current);
      chain.push(current);
      
      // Find all attached neighbors
      const polygon = workspace.getPolygon(current);
      for (const [edgeIdx, attachment] of polygon.attachedTo) {
        if (!visited.has(attachment.targetId)) {
          queue.push(attachment.targetId);
        }
      }
    }
    
    return { id: generateChainId(), polygons: chain };
  }
  
  moveChain(chainId: string, delta: Vector3) {
    const chain = this.chains.get(chainId);
    for (const polygonId of chain.polygons) {
      const polygon = workspace.getPolygon(polygonId);
      polygon.position.addInPlace(delta);
    }
  }
}
```

### Unit Edge Visualization

```javascript
function createUnitEdgePolygon(sides: number, scene: BABYLON.Scene) {
  const unitEdgeLength = 1.0;
  const circumradius = unitEdgeLength / (2 * Math.sin(Math.PI / sides));
  const internalAngle = ((sides - 2) * Math.PI) / sides;
  
  // Generate vertices with unit edges
  const vertices = [];
  for (let i = 0; i < sides; i++) {
    const angle = (i * 2 * Math.PI) / sides;
    vertices.push(new BABYLON.Vector3(
      circumradius * Math.cos(angle),
      0,
      circumradius * Math.sin(angle)
    ));
  }
  
  // Create edges with unit length verification
  const edges = [];
  for (let i = 0; i < sides; i++) {
    const start = vertices[i];
    const end = vertices[(i + 1) % sides];
    const length = BABYLON.Vector3.Distance(start, end);
    
    // Verify unit length (with small tolerance)
    if (Math.abs(length - unitEdgeLength) > 0.001) {
      console.warn(`Edge ${i} length ${length} != unit length ${unitEdgeLength}`);
    }
    
    edges.push({
      index: i,
      start,
      end,
      midpoint: BABYLON.Vector3.Center(start, end),
      length,
      internalAngle,
      isOpen: true
    });
  }
  
  return { vertices, edges, circumradius, internalAngle };
}
```

## GPU/CPU Coordination

### CPU Responsibilities
- Polygon instantiation logic
- Chain detection (BFS traversal)
- Attachment validation
- Edge compatibility checking
- Fold angle calculation
- Unicode structure updates

### GPU Responsibilities
- Mesh rendering
- Visual feedback (highlights, snap guides)
- Edge coloring (RED=open, GREEN=attached)
- Chain visualization
- Smooth movement animations

### Async Decoupling
- CPU: Attachment calculations run async
- GPU: Rendering continues independently
- Updates batched for performance
- Unicode structure updates queued

## Similar 3D Architecture Programs

### Blender
- **Selection**: Click to select, Shift+click for multi-select
- **Movement**: G key (grab), X/Y/Z for axis constraints
- **Rotation**: R key, Shift+R for free rotation
- **Grouping**: Parent-child relationships, move groups together

### Rhino
- **Snapping**: Object snaps, edge snaps
- **Groups**: Group objects, move groups as units
- **Precision**: Unit-based measurements

### SketchUp
- **Components**: Reusable groups
- **Inference**: Smart snapping to edges/vertices
- **Move**: Click-drag, preserves relationships

## Optimization Strategies

### 1. Unit Edge Caching
- Pre-calculate circumradius for all polygon types (3-20)
- Cache edge calculations
- Reuse geometry for identical polygon types

### 2. Chain Caching
- Cache chain detection results
- Only recalculate when attachments change
- Use chain IDs for efficient lookups

### 3. Visual Feedback Optimization
- Render snap guides only when near threshold
- Use instanced rendering for identical polygons
- LOD based on chain complexity

### 4. Unicode Structure Updates
- Batch updates during movement
- Defer updates until movement complete
- Async processing for large chains

## Next Steps

1. ✅ Fix button-based instantiation
2. ✅ Implement workspace movement
3. ✅ Add chain detection
4. ✅ Implement chain movement
5. ✅ Optimize unit edge visualization
6. ✅ Add internal angle representation
7. ✅ Improve GPU/CPU coordination

