# Performance Budgets

**Target Platforms:** Windows, Linux, macOS (Desktop); Console TBD  
**Last Updated:** 2025-10-30

---

## Frame Budget (60 FPS Target)

Target frame time: **16.67ms** (1000ms / 60 frames)

| Phase | Desktop (ms) | Mobile (ms) | Notes |
|-------|--------------|------------|-------|
| **Simulation** | 2.0 | 3.0 | Physics, animation, game logic |
| **Culling / LOD** | 1.0 | 0.5 | Frustum, occlusion, visibility |
| **Rendering CPU** | 1.5 | 2.0 | Command buffer generation, state setup |
| **GPU Wait** | 8.0 | 8.0 | GPU frame lag; frame i-1 GPU completion |
| **UI / Overlay** | 1.0 | 1.0 | HUD, menus, debug overlays |
| **Buffer Swap** | 0.5 | 1.0 | Display presentation |
| **Reserve** | 1.67 | 1.5 | Spikes, scheduler overhead |
| **Total** | **16.67** | **17.0** | Must stay <17ms for 60 FPS |

---

## Memory Budgets

### VRAM Allocation (Per-Platform)

| Pool | Desktop (MB) | Mobile (MB) | Console (MB) | Rationale |
|------|--------------|-----------|--------------|-----------|
| **Render Targets** | 512 | 128 | 1024 | Backbuffer + G-buffers + temp |
| **Textures** | 2048 | 512 | 2048 | Streamed; LRU cache |
| **Meshes** | 1024 | 256 | 2048 | Vertex/index buffers |
| **Pipeline State** | 128 | 32 | 256 | PSO cache + sampler sets |
| **Job System** | 256 | 64 | 256 | Command buffers, job descriptors |
| **Scratch / Transient** | 256 | 32 | 256 | Per-frame allocations |
| **Total VRAM** | **4224 MB** | **1024 MB** | **6144 MB** | Soft cap; alert at 90% |

### RAM Allocation (System Memory)

| Pool | Desktop (MB) | Mobile (MB) | Notes |
|------|--------------|-----------|-------|
| **Physics State** | 128 | 64 | Bodies, constraints, islands |
| **Animation Buffers** | 256 | 64 | Bones, curves, LOD data |
| **Audio** | 256 | 128 | Streaming buffers, effects |
| **Scripting / Game State** | 512 | 256 | Script VM, entity state |
| **Total RAM** | **1152 MB** | **512 MB** | Excludes engine core (~200 MB) |

---

## Draw & Dispatch Budgets

| Metric | Desktop | Mobile | Console | Notes |
|--------|---------|--------|---------|-------|
| **Max Draw Calls** | 4000 | 1000 | 5000 | Per-frame; includes instanced |
| **Max Dispatches** | 500 | 100 | 1000 | Compute shader invocations |
| **Max Vertices/Frame** | 50M | 10M | 100M | Includes overdraw |
| **Max Triangles/Frame** | 20M | 5M | 50M | Post-culling |

---

## Per-Subsystem Budgets

### Rendering

| Metric | Desktop | Mobile | Threshold |
|--------|---------|--------|-----------|
| Frame overhead (CPU) | <1.5ms | <2ms | Before GPU stall |
| Barrier count | <50 | <20 | Per-pass; minimize sync |
| Texture uploads | <10MB/frame | <5MB/frame | Streaming budget |
| Allocator fragmentation | <20% | <15% | Before defrag trigger |

### Physics

| Metric | Desktop | Mobile | Threshold |
|--------|---------|--------|-----------|
| Broad-phase | <0.5ms | <0.5ms | SAP or DBVT |
| Narrow-phase | <1ms | <0.5ms | Island processing |
| Solver iterations | 4 | 2 | Fixed |
| Constraint resolves | <1ms | <0.5ms | Warm-starting enabled |

### Animation

| Metric | Desktop | Mobile | Threshold |
|--------|---------|--------|-----------|
| Bone updates | <0.3ms | <0.2ms | Dual-quat blending |
| Skinning | <0.8ms | <0.5ms | GPU-resident matrices |

### Asset Streaming

| Metric | Desktop | Mobile | Threshold |
|--------|---------|--------|-----------|
| Import overhead | <100ms | <100ms | One-time per scene |
| Hot-reload latency | <200ms | <200ms | Material/mesh changes |

---

## CI Performance Gates

### Regression Detection

```yaml
perf_gates:
  frame_time_regression:
    threshold: 5%  # Block if >5% slower than baseline
    
  draw_call_increase:
    threshold: 100  # Block if >100 additional draw calls
    
  memory_growth:
    threshold: 50MB  # Block if RSS grows >50MB
    
  shader_compile_time:
    threshold: 10%   # Warn if >10% slower
```

### Per-Build Checks

- ✅ Frame budget: Median frame time <16.67ms @ 60fps
- ✅ Draw calls: <4000 on reference scene (desktop)
- ✅ Memory: Peak RSS <2GB during load (desktop)
- ✅ Startup time: <3s from exe launch to first frame
- ✅ Asset import: <100ms per typical mesh

---

## Dashboard Metrics

### Real-Time Dashboards

1. **Frame Timing**
   - Median, p95, p99 frame times per platform
   - Histogram of frame times (detect bimodal distributions)
   - CPU vs GPU frame breakdown

2. **Memory Usage**
   - VRAM pool utilization over time
   - Fragmentation trend per pool
   - Peak allocations per subsystem

3. **Draw Efficiency**
   - Draw call count, dispatch count
   - Triangles per frame, overdraw ratio
   - State change frequency

4. **Regression Tracking**
   - Commit-by-commit frame time trend
   - Memory growth rate
   - VRAM pool trending

---

## Tuning Guidelines

### When to Tune Down (Save Budget)

- **Excess capacity:** >30% margin on frame time? Reduce draw call pre-allocation or LOD aggressiveness.
- **Unused memory pools:** Reallocate to higher-demand pool or shrink.
- **Sparse dispatches:** Combine compute workloads.

### When to Tune Up (Improve Quality)

- **Visual regressions:** Add back effects (parallax, shadows) within budget expansion.
- **Frame spikes:** Add more buffer for VRR adaptation or time smoothing.
- **Mobile bottleneck:** Add extra physics or animation detail if <1ms spare on desktop.

---

## Validation

**Per Release:**
- ✅ Run perf suite 3× on reference rig; confirm median stable
- ✅ Capture golden metrics (frame time, draw calls, memory) per platform
- ✅ Compare vs. previous release; alert if >5% regression
- ✅ Archive baseline for future comparisons

---

## References

- STAB-001 (SLOs)
- STAB-004 (this document)
- STAB-051 (CI perf gates)
- EXECUTION_ROADMAP.md (overall timeline)
