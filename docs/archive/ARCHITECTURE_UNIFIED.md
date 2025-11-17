# Polylog6: Unified Architecture Documentation

## Executive Summary

**Polylog6** is a hierarchical polyform (polygon-based structure) compression and discovery system that enables users to design, compose, and discover novel geometric structures through a tiered symbolic representation system.

**Core Vision:** Enable users to work with complex geometric structures at multiple abstraction levels (primitives → polyhedra → custom compositions → discovered patterns) with automatic compression, validation, and promotion through a tier system.

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer (React + Babylon.js)      │
├─────────────────────────────────────────────────────────────┤
│  Workspace Manager │ GPU Warming │ Tier 0 Visualization    │
├─────────────────────────────────────────────────────────────┤
│                    Service Layer (FastAPI)                  │
├─────────────────────────────────────────────────────────────┤
│  Detection Engine │ Compression System │ Catalog Manager   │
├─────────────────────────────────────────────────────────────┤
│                    Data Layer (Unicode Tiers)               │
├─────────────────────────────────────────────────────────────┤
│  Tier 0: Attachments │ Tier 1: Polyhedra │ Tier 2+: Assemblies│
└─────────────────────────────────────────────────────────────┘
```

### Backend (Python)

- **FastAPI** - REST API server
- **Unified Geometry Backend** - Netlib integration for precomputed polyhedra
- **Tiered Storage** - Unicode compression system (Series A/B/C/D)
- **Tier Generation** - Tier 1 (Platonic/Archimedean/Johnson) and Tier 2+ decomposition
- **Detection Pipeline** - Image segmentation, pattern analysis, topology detection
- **Monitoring System** - Telemetry, alerts, performance tracking

### Frontend (React + Babylon.js)

- **React** - UI framework
- **Babylon.js** - 3D rendering engine
- **Workspace Manager** - Polygon interaction system
- **GPU Warming** - Precomputed chain caching
- **Async CPU Pipeline** - Pre-warming GPU buffers with Tier 0 symbols

### Desktop (Tauri)

- **Rust** - Desktop wrapper
- **Python Bridge** - Backend integration

---

## Core Concepts

### Primitives

- **Definition**: 3-20 sided polygons
- **Unit Edge Length**: 1.0 (all edges = 1.0 unit)
- **Properties**:
  - Sides: 3-20
  - Internal angle: `(n-2) * 180 / n`
  - Circumradius: `R = 1.0 / (2 * sin(π/n))`
- **Note**: Primitives are NOT Tier 0. They are a separate structure.

### Tier 0: Polygon-to-Polygon Attachments

- **Purpose**: Encode attachment sequences between polygons
- **Encoding**: Series A/B/C/D + subscript (1-999)
- **Series Structure** (canonical from `tier0_generator.py`):
  - **Series A**: [3, 4, 5, 6, 7, 8, 9, 10, 11] - positions 1-9
  - **Series B**: [20, 4, 6, 8, 10, 12, 14, 16, 18] - positions 1-9
  - **Series C**: [3, 6, 9, 12, 15, 18, 8, 7, 10] - positions 1-9
  - **Series D**: [14, 20, 13, 11, 4, 16, 17, 5, 19] - positions 1-9
- **Total**: 36 base positions (4 series × 9 positions)
- **Capacity**: 2000+ attachment sequences via subscript encoding

### Tier 1: Known Polyhedra

- **Platonic solids**: 5 (tetrahedron, cube, octahedron, dodecahedron, icosahedron)
- **Archimedean solids**: 13
- **Johnson solids**: 92+
- **Total**: 110 known polyhedra
- **Generation**: Using symmetry operations
- **Storage**: JSONL format with LOD metadata

### Tier 2: Runtime-Generated Candidates

- **Source**: User compositions created in workspace
- **Format**: Attachment sequences with metadata
- **Storage**: `storage/caches/tier_candidates.jsonl`
- **Promotion**: Validated candidates promoted to Tier 3

### Tier 3: Promoted Structures

- **Source**: Tier 2 candidates that meet promotion criteria
- **Criteria**:
  - Stability ≥ 0.85
  - Valid composition (all polygons valid)
  - No overlaps or conflicts
  - Unique structure
- **Storage**: Tier 3 catalog
- **Purpose**: Discovered patterns library

---

## Unicode Compression System

### Compression Strategy

The system uses a 4-level Unicode compression strategy:

#### Level 0: Polygon Labels

- A = Triangle (3 sides)
- B = Square (4 sides)
- C = Pentagon (5 sides)
- D = Hexagon (6 sides)
- ... up to R = 20-gon

#### Level 1: Pair Compression

- AA → α (U+03B1)
- AB → β (U+03B2)
- BB → γ (U+03B3)
- etc.

#### Level 2: Cluster Encoding

Format: `<symbol>⟨n=<count>, θ=<angle>°, σ=<symmetry>⟩`

#### Level 3: Recursive Structures

- Tier 0 references within Tier 2+ structures
- Hierarchical compression

### Compression Ratios

- **Target**: 4:1 to 20:1 compression
- **Current**: 1.0-10.0 (varies by structure)
- **LOD Levels**: 4 levels (full, medium, low, thumbnail)

---

## Async & Decoupling Architecture

### CPU/GPU Coordination

#### CPU Responsibilities

- Polygon instantiation logic
- Chain detection (BFS traversal)
- Attachment validation
- Edge compatibility checking
- Fold angle calculation
- Unicode structure updates
- Tier 0 encoding/decoding

#### GPU Responsibilities

- Mesh rendering
- Visual feedback (highlights, snap guides)
- Edge coloring (RED=open, GREEN=attached)
- Chain visualization
- Smooth movement animations
- LOD switching

### Async Decoupling Patterns

#### 1. Async CPU Pipeline

```javascript
// Frontend: AsyncCPUPipeline
// Runs ahead of GPU, streams attachment data asynchronously
// GPU never waits on CPU
class AsyncCPUPipeline {
  async loadPrecomputedTier0() { /* ... */ }
  async warmGPU(symbols) { /* ... */ }
}
```

#### 2. Background Tasks (Backend)

```python
# FastAPI: BackgroundTasks
@router.post("/analyze_async")
def analyze_async(request, background: BackgroundTasks):
    background.add_task(_invoke_async, task)
    return {"status": "accepted"}
```

#### 3. Thread Pool Executor

```python
# Detection Service: ThreadPoolExecutor
class ImageDetectionService:
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    def analyze_async(self, task, callback=None):
        future = self._executor.submit(self.analyze, task)
        if callback:
            future.add_done_callback(lambda fut: callback(fut.result()))
```

#### 4. Queue-Based Telemetry

```python
# Monitoring: Queue-based async processing
class ImageDetectionService:
    def __init__(self):
        self._telemetry_queue = Queue(maxsize=64)
        self._telemetry_thread = Thread(target=self._telemetry_loop, daemon=True)
        self._telemetry_thread.start()
```

### Service Boundaries

#### Detection Service

- **Interface**: `DetectionTask` → `dict[str, Any]`
- **Async Method**: `analyze_async(task, callback)`
- **Decoupling**: ThreadPoolExecutor for CPU-intensive work

#### Monitoring Service

- **Interface**: `get_monitoring_service()` → `MonitoringService`
- **Decoupling**: Queue-based telemetry ingestion
- **Async**: Background thread for telemetry processing

#### Storage Service

- **Interface**: REST API endpoints
- **Decoupling**: FastAPI async handlers
- **Pattern**: Request/response with background tasks

#### Workspace Manager

- **Interface**: Event-driven polygon operations
- **Decoupling**: GPU rendering independent of CPU calculations
- **Pattern**: Batched updates for performance

---

## Data Flow

### 1. User Interaction Flow

```
User Interaction → Workspace Manager → Tier 0 Encoding → Backend Indexing → Unicode Storage
```

### 2. Visualization Flow

```
Polygon Placement → Chain Detection → Atomic Chain Library → Babylon.js Rendering
```

### 3. Discovery Flow

```
User Composition → Tier 2 Candidate → Validation → Promotion → Tier 3 Library
```

### 4. Compression Flow

```
Geometric Structure → Tier 0 Encoding → Unicode Symbol → LOD Compression → Storage
```

---

## Workspace Interaction Model

### Core Principles

1. **Unit Edge Length**: All edges = 1.0 unit across entire workspace
2. **Button-Based Instantiation**: User selects polygon from slider, clicks "Add to Workspace"
3. **Click-and-Drag Movement**: Click polygon to select, drag to move
4. **Automatic Edge Snapping**: System detects edge proximity, provides visual feedback
5. **Chain/Subform Movement**: Attached polygons move together as units

### Interaction Phases

#### Phase 1: Polygon Instantiation

- Method: Button-based (NOT drag-drop)
- User selects polygon from slider (A-R)
- Clicks "Add to Workspace" button
- Polygon appears at default position
- All edges start as **open** (available for attachment)

#### Phase 2: Individual Polygon Movement

- Method: Click-and-drag within workspace
- Click polygon to select
- Drag to move freely
- **Rotation**: Hold Shift while dragging
- Visual feedback: Highlight selected polygon

#### Phase 3: Edge Attachment

- Method: Automatic snapping when edges align
- Move polygon near another polygon
- System detects edge proximity (< threshold)
- Visual feedback: Green snap guides on compatible edges
- Drop to attach: Edges snap edge-to-edge
- Fold angle applied based on polygon types
- Attached edges marked as **closed**

#### Phase 4: Chain/Subform Movement

- Method: Move attached groups as units
- Once polygons are attached, they form a **chain** or **subform**
- Click any polygon in chain to select entire chain
- Drag to move entire chain/subform together
- All attachments preserved during movement

---

## Testing Architecture

### Unified Interactive Development Service

**Location**: `scripts/unified_interactive_dev.py`

**Purpose**: Launch the actual program (API + Frontend) with integrated testing support for interactive development.

**Features**:

- Starts API server (FastAPI on port 8000)
- Starts Frontend dev server (Vite on port 5173)
- Optional: Runs Playwright tests in interactive mode
- Tracks user interactions during development
- Clean shutdown of all processes

**Usage**:

```bash
# Start dev environment
python scripts/unified_interactive_dev.py

# Start dev + run tests
python scripts/unified_interactive_dev.py --test

# Start API only
python scripts/unified_interactive_dev.py --api-only

# Start frontend only
python scripts/unified_interactive_dev.py --frontend-only
```

### Test Types

#### Unit Tests

- **Location**: `tests/`
- **Framework**: pytest
- **Coverage Target**: 95%+

#### Integration Tests

- **Location**: `src/frontend/tests/integration/`
- **Framework**: Playwright
- **Focus**: Backend-frontend integration

#### Visual Tests

- **Location**: `src/frontend/tests/visual/`
- **Framework**: Playwright
- **Mode**: Headed (visible browser)

#### Performance Tests

- **Location**: `src/frontend/tests/performance/`
- **Metrics**: FPS, memory usage, API response time

---

## Development Workflow

### Quick Start

```bash
# Start unified interactive development
python scripts/unified_interactive_dev.py

# Or use unified launcher
python scripts/unified_launcher.py dev
```

### Testing

```bash
# Run all tests
python scripts/automated_test_suite.py --type all

# Run interactive tests
python scripts/unified_interactive_dev.py --test

# Run Playwright tests manually
cd src/frontend && npx playwright test --headed
```

### Building

```bash
# Build complete application
python scripts/unified_launcher.py build

# Build frontend only
python scripts/unified_launcher.py build:frontend
```

---

## Key Files

### Backend

- `src/polylog6/api/main.py` - API entry point
- `src/polylog6/storage/tier0_generator.py` - Tier 0 encoding
- `src/polylog6/geometry/unified_backend.py` - Unified geometry system
- `src/polylog6/detection/service.py` - Image detection service
- `src/polylog6/monitoring/service.py` - Monitoring service

### Frontend

- `src/frontend/src/utils/workspaceManager.js` - Workspace management
- `src/frontend/src/components/BabylonScene.jsx` - 3D rendering
- `src/frontend/src/utils/tier0Encoder.js` - Tier 0 encoding/decoding
- `src/frontend/src/utils/gpuWarmingManager.js` - GPU warming pipeline

### Testing

- `scripts/unified_interactive_dev.py` - Unified interactive dev service
- `src/frontend/tests/integration/unified-interactive-test.spec.js` - Interactive tests
- `scripts/automated_test_suite.py` - Automated test suite

### Documentation

- `docs/ARCHITECTURE_UNIFIED.md` - This file (unified architecture)
- `docs/WORKSPACE_INTERACTION_ARCHITECTURE.md` - Interaction model details
- `docs/INTEGRATION_ROADMAP.md` - Integration phases

---

## Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Polyhedra list load | <100ms | ⏳ Test |
| Single polyhedron load | <50ms | ⏳ Test |
| LOD switch | <16ms | ⏳ Test |
| Rendering FPS | 60 | ⏳ Test |
| API response time | <100ms | ⏳ Test |
| Compression ratio | 4:1-20:1 | ✅ Achieved |
| Memory usage | <100MB | ⏳ Test |

---

## Integration Roadmap

### Phase 1: Engine Validation (Current)

- Validate all engine structures
- Run comprehensive test suite
- Verify API endpoints
- Test storage persistence

### Phase 2: Advanced Generation

- Multi-polygon generation (3+ polygons)
- Seed-based generation from discovered polyforms
- Exponential growth modes
- Pattern detection integration

### Phase 3: Tier Promotion System

- Tier 2 → Tier 3 promotion
- Stability threshold validation
- Closure detection
- Symbol registry updates

### Phase 4: Full Workspace Integration

- Interactive 3D manipulation
- Drag-and-drop polygon placement
- Real-time attachment validation
- Visual feedback systems

### Phase 5: Advanced Features

- Image detection integration
- Pattern discovery engine
- Telemetry and monitoring
- Performance optimization

---

## See Also

- `README.md` - Quick start guide
- `docs/DEVELOPMENT.md` - Development guide
- `docs/WORKSPACE_INTERACTION_ARCHITECTURE.md` - Detailed interaction model
- `documentation/PROJECT_SCOPE_AND_BLOCKERS.md` - Project scope and blockers
