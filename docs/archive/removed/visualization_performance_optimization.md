# Visualization Performance Optimization & Interaction Research

**Purpose:** Identify gaps in the current visualization architecture and synthesize proven patterns for smooth, responsive 3D interaction with polyform assemblies.

---

## 1. Current Visualization Stack Assessment

### 1.1 Declared Technology (From Specs)
- **Frontend:** React + Three.js / React Three Fiber
- **Desktop Wrapper:** Tauri (Rust) with FastAPI backend
- **Rendering Target:** WebGL (Three.js ≥0.157)
- **State Management:** Zustand
- **Performance Requirements:**
  - ≥30 FPS for assemblies with 1 000+ polygons
  - Sub-100 ms interaction latency (click, drag, rotate)
  - Progressive visualization (AABB first → full geometry)
  - Rendering memory budget ≤200 MB; total ≤500 MB

### 1.2 Potential Gaps
| Gap Area                | Risk   | Evidence                                                         |
|-------------------------|--------|------------------------------------------------------------------|
| GPU instancing          | Medium | Spec references instancing; no implementation documented         |
| Frustum culling         | Medium | No culling strategy noted                                        |
| LOD management          | High   | LOD metadata planned; runtime loading undocumented               |
| Worker thread offloading| High   | Heavy geometry operations risk blocking UI thread                |
| Input handling          | Medium | Click/context menu flows undefined                               |
| Memory profiling tools  | Low    | No enforcement of 200 MB rendering budget                        |

---

## 2. Three.js Performance Optimization

### 2.1 Official Performance Guidance
- **Resource:** [Three.js – How to update things](https://threejs.org/docs/#manual/en/introduction/How-to-update-things)
- **Key Practices:** BufferGeometry, InstancedMesh, frustum culling, texture atlases
- **Polyform Applications:**
  - InstancedMesh for repeat assemblies (single draw call)
  - `geometry.computeBoundingSphere()` to ensure culling
  - Reuse shared materials to minimize state changes

### 2.2 React Three Fiber (R3F) Patterns
- **Resource:** [R3F Performance Pitfalls](https://docs.pmnd.rs/react-three-fiber/advanced/pitfalls)
- **Highlights:**
  - Memoize geometry/material creation with `useMemo`
  - Mutate in-place inside `useFrame` (avoid re-renders)
  - Leverage built-in pointer events for selections

### 2.3 GPU Instancing Strategy
- **Resource:** [Three.js Instancing Example](https://threejs.org/examples/#webgl_instancing_dynamic)
- **Usage:**
  - Create `InstancedMesh` for repeated subassemblies
  - Update transforms via `instanceMatrix`
  - Target 50–100× draw call reduction when 10+ identical units exist

---

## 3. Level of Detail (LOD) & Progressive Loading

### 3.1 Three.js LOD API
- **Resource:** [LOD docs](https://threejs.org/docs/#api/en/objects/LOD)
- **Spec-aligned thresholds:**
  - <5 units → full detail
  - 5–20 units → simplified meshes
  - >20 units → bounding boxes or icons

### 3.2 Mesh Simplification & Catalog Integration
- **Library:** `BufferGeometryUtils.simplifyModifier`
- **Workflow:**
  - During catalog generation, produce `full`, `medium`, `low` meshes
  - Store results in `catalogs/lod_metadata.json`

### 3.3 Progressive Geometry Loading
- **Pattern:** AABB-first render, asynchronous upgrade to full geometry (~100 ms delay)
- **Goal:** 50 ms AABB render, 90 ms full upgrade to match spec targets

---

## 4. Interaction Architecture

### 4.1 Pointer Events & Context Menus
- **Resource:** [R3F Events](https://docs.pmnd.rs/react-three-fiber/api/events)
- **Implementation:**
  - `onClick`, `onContextMenu`, `onPointerDown/Up/Move`
  - Use `react-contexify` (≈5 KB) for lightweight context menus

### 4.2 Selection State (Zustand)
- Maintain `selectedPolyforms` set
- Provide `select`, `deselect`, `clearSelection` actions
- Highlight selection via emissive/material adjustments

---

## 5. Worker Thread Offloading

### 5.1 Web Workers with Comlink
- **Use Cases:** CGAL hull computation, mesh simplification, collision detection
- **Pattern:** Expose worker API with `comlink`; call asynchronously from UI

### 5.2 R3F Concurrent Mode
- Enable `concurrent` canvas with `frameloop="demand"` to prioritize user interactions and reduce unnecessary renders

---

## 6. Memory Profiling & Enforcement

### 6.1 Tooling
- Chrome DevTools memory profiler to detect leaks (detached geometries)
- `stats.js` (memory panel) for real-time monitoring

### 6.2 Budget Enforcement
- Monitor `renderer.info.memory`
- Downgrade LOD when geometry memory exceeds 200 MB

### 6.3 Disposal Hooks
- Custom `useDisposableGeometry` hook to dispose geometry/materials/textures on unmount or LOD switch

---

## 7. Underutilized Three.js Features

- **Object Pooling:** Reuse meshes for rapid add/remove scenarios
- **Render Targets:** Cache complex subassemblies as textures
- **InstancedBufferGeometry:** Encode per-instance attributes (e.g., selection state) without material duplication

---

## 8. Tauri-Specific Optimizations

- Enable native window decorations to reduce memory overhead
- Set WebView memory limits (`--max-old-space-size=4096`)
- Use Tauri IPC (`invoke`) for direct Rust → JS data transfer; reserve FastAPI for compute-heavy backends

---

## 9. Testing & Validation

- **Puppeteer:** Automated FPS benchmarks (≥30 FPS target)
- **Storybook Storyshots:** Visual regression snapshots of scenes
- **Manual stress tests:** 5 000 polyforms to verify graceful degradation

---

## 10. Recommended Action Plan

| Phase | Focus                         | Duration | Key Tasks                                             |
|-------|-------------------------------|----------|-------------------------------------------------------|
| 1     | Foundation                    | Week 1   | GPU instancing, LOD system, disposal hooks            |
| 2     | Interaction                   | Week 2   | Pointer events, context menus, progressive loading    |
| 3     | Optimization                  | Week 3   | Worker offloading, memory monitoring, Tauri IPC       |
| 4     | Validation                    | Week 4   | Performance suite, stress tests, user acceptance      |

Success metrics: ≥30 FPS @1 000 polyforms, click response <100 ms, render memory ≤200 MB.

---

## 11. Dependency Recommendations

- **Add:** `react-contexify`, `stats.js`
- **Dev:** `puppeteer`, `@storybook/addon-storyshots`
- **Optional:** `comlink`, `@react-three/rapier`, `@blueprintjs/core`

---

## 12. Leveraging Existing Dependencies

- **Trimesh:** Use for offline mesh decimation (LOD generation)
- **SciPy:** `KDTree` for instancing detection
- **NumPy:** Vectorized transform calculations before GPU uploads

---

## 13. Visualization Research References

- **Books:** *Three.js Cookbook* (Dirksen), *Real-Time Rendering* (Akenine-Möller et al.), *WebGL Insights*
- **Guides:** discoverthreejs.com tips, WebGL Fundamentals on instancing, PMNDRS R3F performance blog

---

## 14. Success Metrics & Validation

| Metric            | Target  | Validation Method                   |
|-------------------|---------|-------------------------------------|
| FPS (1 000 polys) | ≥30     | Puppeteer measurement               |
| Click latency     | <100 ms | React Profiler / performance marks  |
| Render memory     | <200 MB | stats.js + heap snapshots           |
| LOD coverage      | 3 levels| Manual + automated tests            |
| Instancing usage  | >50 %   | Instrumentation logs                |
| AABB render time  | <50 ms  | `performance.now()` markers         |
| Full upgrade time | <90 ms  | `performance.now()` markers         |

---

## 15. Integration Checklist

- [ ] Review Three.js & R3F performance docs
- [ ] Implement instancing + LOD + disposal hooks
- [ ] Wire pointer/context menu interactions
- [ ] Add progressive loading component
- [ ] Introduce worker offloading for topology/LOD tasks
- [ ] Integrate memory monitoring + budget enforcement
- [ ] Migrate catalog fetches to Tauri IPC
- [ ] Establish automated performance & visual regression tests
- [ ] Document instrumentation & update specifications

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-09  
**Next Review:** After Phase 1 (Week 1) implementation
