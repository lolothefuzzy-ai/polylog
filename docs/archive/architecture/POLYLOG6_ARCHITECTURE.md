# Polylog6 Architecture Overview

**Version:** 2.0  
**Last Updated:** 2025-11-15  
**Purpose:** Consolidated architectural documentation for the Polylog6 polyform simulator system.

---

## Executive Summary

Polylog6 is a desktop application for generating, visualizing, and analyzing 3D polyform assemblies. The system uses a hybrid detection approach combining CGAL geometric processing with Unicode-based compression for efficient storage and retrieval of polyform structures.

### Key Capabilities
- Real-time 3D visualization with sub-100ms interaction latency
- Automated assembly generation across 6 expansion patterns
- Mathematical precision with O/I combinatorial metrics
- Memory efficiency via cascading reference architecture (~500MB budget)
- Cross-platform deployment (Windows, macOS, Linux)

### Technology Stack
- **Frontend:** React + Three.js/React Three Fiber + Zustand
- **Desktop:** Tauri (Rust) wrapper
- **Backend:** FastAPI (Python) with CGAL integration
- **Storage:** Tiered Unicode compression system
- **Testing:** Playwright + pytest

---

## System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Desktop Layer (Tauri)                    │
├─────────────────────────────────────────────────────────────┤
│  React Frontend │ Three.js Renderer │ State Management      │
├─────────────────────────────────────────────────────────────┤
│                    Service Layer (FastAPI)                  │
├─────────────────────────────────────────────────────────────┤
│  Detection Engine │ Compression System │ Catalog Manager    │
├─────────────────────────────────────────────────────────────┤
│                    Data Layer (Unicode Tiers)              │
├─────────────────────────────────────────────────────────────┤
│  Tier 0: Primitives │ Tier 1: Polyhedra │ Tier 2+: Assemblies│
└─────────────────────────────────────────────────────────────┘
```

### 1. Detection & Analysis Pipeline

**Track A: Detection Pipeline**
- **ImageSegmenter:** Felzenszwalb + K-means for region detection
- **PatternAnalyzer:** FFT + symmetry analysis for pattern recognition
- **TopologyDetector:** CGAL/Trimesh for hull computation and topology
- **CandidateOptimizer:** NSGA-lite for optimization

**Track B: Monitoring Loop**
- **LibraryRefreshWorker:** Catalog updates and registry maintenance
- **MonitoringDispatcher:** Telemetry collection and distribution
- **ContextBriefTailer:** Real-time monitoring dashboards

### 2. Compression Architecture

The system uses a 4-level Unicode compression strategy:

#### Level 0: Polygon Labels
```
A = Triangle (3 sides)    B = Square (4 sides)
C = Pentagon (5 sides)   D = Hexagon (6 sides)
...
R = 20-gon
```

#### Level 1: Pair Compression
```
AA → α (U+03B1)  AB → β (U+03B2)  BB → γ (U+03B3)
```

#### Level 2: Cluster Encoding
```
Format: <symbol>⟨n=<count>, θ=<angle>°, σ=<symmetry>⟩
Example: Ω₁⟨n=6, θ=70.5°, σ=T⟩ (Tetrahedron)
```

#### Level 3: Assembly Encoding
```
Format: <cluster_sequence>⟨symmetry⟩
Example: Ω₁²Ω₂⟨σ=C₂⟩ (Bridge structure)
```

#### Level 4: Mega-Structure Encoding
```
Format: <assembly_symbol><pattern>⟨params⟩
Example: Ψ₁⟨radial, n=12, r=5.0, σ=D₁₂⟩
```

### 3. Memory Reduction Performance

| Structure | Polygon Count | Naive Storage | Compressed Storage | Ratio |
|-----------|--------------|---------------|-------------------|-------|
| Single polygon | 1 | 500 bytes | 1 byte | 500:1 |
| Small cluster | 10 | 5 KB | ~50 bytes | 100:1 |
| Assembly | 200 | 100 KB | ~500 bytes | 200:1 |
| Mega-structure | 1000 | 500 KB | ~100 bytes | 5000:1 |

### 4. Unicode Symbol Allocation

The system uses O(1) Unicode symbol allocation for 40,000+ unique polyforms:

- **Tier 1:** Primitives (A-R) + Greek pairs (α-ω)
- **Tier 2:** Standard polyhedra (Platonic, Archimedean, Johnson)
- **Tier 3:** User clusters and flexible assemblies
- **Tier 4:** Mega-structures and archive

**Performance:** Sub-microsecond symbol allocation and lookup via direct code-point indexing.

---

## Key Systems

### 1. Storage System

**Tiered Storage Architecture:**
```
catalogs/
├── tier0/          # Primitive polygons (18 types)
├── tier1/          # Standard polyhedra (110 solids)
├── tier2/          # User-defined clusters
├── tier3/          # Complex assemblies
└── attachments/    # Pairwise attachment data
```

**API Endpoints:**
- `GET /tier1/polyhedra` - List all polyhedra
- `GET /tier1/polyhedra/{symbol}` - Get specific polyhedron with LOD
- `GET /tier1/attachments/{a}/{b}` - Get attachment options
- `GET /tier1/stats` - System statistics

### 2. Visualization System

**Performance Requirements:**
- ≥30 FPS for 1000+ polygon assemblies
- <100ms interaction latency
- ≤200MB rendering memory budget

**Optimization Strategies:**
- **GPU Instancing:** Single draw calls for repeated assemblies
- **LOD Management:** Progressive loading (AABB → full geometry)
- **Frustum Culling:** Automatic viewport culling
- **Worker Offloading:** Heavy geometry operations in web workers

**LOD Levels:**
- **Full:** <5 units distance
- **Medium:** 5-20 units
- **Low:** >20 units
- **Thumbnail:** Icons/bounding boxes

### 3. Simulation Engine

**Core Components:**
- **LiaisonGraph:** Topological representation of connections
- **OpenEdgeRegistry:** Track available attachment points
- **ParametricFoldSequence:** Cached fold angle calculations
- **AssemblyDecompositionTree:** Hierarchical breakdown for analysis
- **GeometryRuntime:** Event-driven simulation processing
- **CheckpointSummary:** State persistence and recovery

**Stability Analysis:**
- Fold angle validation with stability thresholds
- Constraint propagation for placement domains
- Combinatorial O/I metrics calculation

### 4. Discovery System

**Core Components:**
- **VisualizationCommitmentThreshold:** Rules for closure discovery
- **CommitmentDecision:** Enum for acceptance/rejection reasons
- **Tier-based filtering:** High-tier structure prioritization
- **Symmetry analysis:** Exceptional symmetry group detection

**Closure Discovery Logic:**
- High tier (≥5) + high closure (≥0.88) → Auto-commit
- Exceptional symmetry (T,O,I) + priority ≥12.0 → Commit
- Very high priority (≥18.0) → Auto-commit

### 5. Monitoring System

**Core Components:**
- **MonitoringLoop:** Central monitoring orchestration
- **ContextBriefTailer:** Real-time log monitoring
- **LibraryRefreshWorker:** Catalog maintenance
- **DetectionTelemetryBridge:** Event telemetry forwarding
- **AlertSystem:** Threshold-based alerting

**Monitoring Features:**
- Registry state monitoring
- Performance metrics collection
- Alert generation and dispatch
- Context brief file watching

---

## Development Architecture

### 1. Source Code Structure

```
src/polylog6/
├── detection/          # Image processing and pattern detection
├── simulation/         # Physics and assembly simulation
├── compression/        # Unicode compression engine
├── monitoring/         # Telemetry and dashboards
└── api/               # FastAPI endpoints
```

### 2. Testing Architecture

**Unit Tests:** pytest with 95%+ coverage target
**Integration Tests:** Playwright for browser-based testing
**Performance Tests:** Automated FPS and memory benchmarks
**Visual Regression:** Storybook snapshots for UI components

### 3. Build & Deployment

**Development:** Hot reload with vite dev server
**Production:** Tauri build with optimized Rust backend
**CI/CD:** GitHub Actions with multi-platform builds

---

## Data Flow Architecture

### 1. Ingestion Pipeline

```
Raw Images → Segmentation → Pattern Analysis → Topology Detection → Compression → Storage
```

### 2. Runtime Pipeline

```
User Input → Validation → Assembly Generation → Visualization → Telemetry
```

### 3. Monitoring Pipeline

```
System Events → Telemetry Bridge → Monitoring Dispatcher → Dashboards/Alerts
```

---

## Integration Points

### 1. External Libraries

- **CGAL:** Computational geometry for hull operations
- **Three.js:** 3D rendering and WebGL management
- **React Three Fiber:** React integration for Three.js
- **FastAPI:** High-performance API framework
- **Zustand:** Lightweight state management

### 2. System Services

- **Image Detection Service:** Pattern recognition and analysis
- **Compression Service:** Unicode encoding/decoding
- **Catalog Service:** Polyform metadata management
- **Monitoring Service:** Real-time system health

### 3. Data Exchange Formats

- **JSONL:** Line-delimited JSON for streaming data
- **Unicode Symbols:** Compressed representation for polyforms
- **Binary Buffers:** Efficient geometry data transfer

---

## Performance Architecture

### 1. Memory Management

**Budget Allocation:**
- Rendering: ≤200MB
- Catalogs: ≤100MB
- System: ≤200MB
- **Total:** ≤500MB

**Optimization Techniques:**
- Cascading references to avoid duplication
- Lazy loading for large assemblies
- Automatic garbage collection for unused geometries

### 2. Computational Performance

**Target Metrics:**
- Symbol allocation: <1µs per operation
- Geometry processing: <16.67ms (60fps)
- API response: <50ms for catalog queries
- File I/O: <100ms for compression operations

### 3. Caching Strategy

**Multi-Level Caching:**
- **L1:** In-memory symbol cache (hot data)
- **L2:** Disk-based catalog cache (warm data)
- **L3:** Network-based asset cache (cold data)

---

## Security Architecture

### 1. Data Protection

- **Input Validation:** All user inputs sanitized
- **File Access:** Sandboxed file system access
- **Network Security:** HTTPS-only for external communications

### 2. Code Security

- **Memory Safety:** Rust backend prevents buffer overflows
- **Type Safety:** TypeScript for frontend type checking
- **Dependency Scanning:** Automated vulnerability detection

---

## Monitoring & Observability

### 1. Telemetry Collection

**Metrics Tracked:**
- System performance (FPS, memory, CPU)
- User interactions (clicks, drags, assembly operations)
- Error rates and system health
- Feature usage statistics

### 2. Alerting System

**Alert Conditions:**
- Performance degradation (>20% below targets)
- Error rate spikes (>5% failure rate)
- Memory usage approaching limits
- Service availability issues

### 3. Debugging Tools

- **Performance Profiler:** Real-time performance monitoring
- **Event Logger:** Detailed interaction tracking
- **System Dashboard:** Overview of all system components

---

## Future Architecture Evolution

### 1. Scalability Plans

- **Cloud Processing:** Optional cloud backend for heavy computations
- **Distributed Caching:** Multi-node cache for large deployments
- **Microservices:** Service decomposition for team scaling

### 2. Technology Roadmap

- **WebAssembly:** Performance-critical computations in browser
- **WebGPU:** Next-generation graphics API
- **Machine Learning:** AI-assisted pattern recognition
- **Advanced Compression:** Research into new compression algorithms

### 3. Integration Opportunities

- **CAD Systems:** Import/export for professional workflows
- **3D Printing:** Direct manufacturing integration
- **Educational Platforms:** STEM learning applications
- **Research Tools:** Academic collaboration features

---

## Architecture Decision Records

### ADR-001: Unicode Compression Strategy
**Decision:** Use Unicode-based compression for polyform storage
**Rationale:** 100-5000x compression ratios with O(1) lookup performance
**Consequences:** Requires Unicode allocation strategy but provides massive memory savings

### ADR-002: Hybrid Detection Approach
**Decision:** Combine CGAL geometric processing with pattern recognition
**Rationale:** CGAL provides precision, pattern recognition provides speed
**Consequences:** Complex integration but optimal performance/accuracy balance

### ADR-003: Tauri Desktop Wrapper
**Decision:** Use Tauri instead of Electron for desktop deployment
**Rationale:** 5x smaller app size, better performance, Rust security
**Consequences:** Learning curve but superior user experience

---

## Documentation References

- **Integration Roadmap:** `documentation/INTEGRATION_ROADMAP.md`
- **API Documentation:** `documentation/docs/api/`
- **User Guides:** `documentation/docs/user/`
- **Development Guides:** `documentation/docs/development/`

---

## Contact & Support

- **Architecture Issues:** Create GitHub issue with "architecture" label
- **Performance Issues:** Include telemetry data in bug reports
- **Integration Questions:** Reference integration architecture documents

---

*This document consolidates and replaces the following architecture documents:*
- *architecture_overview.md*
- *POLYFORM_SIMULATOR_COMPREHENSIVE_SPEC.md*
- *POLYFORM_COMPRESSION_ARCHITECTURE.md*
- *POLYFORM_DICTIONARY_SYSTEM.md*
- *polyform_backbone_architecture.md*
- *unicode_symbol_allocation_strategy.md*
- *visualization_performance_optimization.md*
- *detection_monitoring_architecture_image.md*
- *polyform_simulator_architecture_research.md*