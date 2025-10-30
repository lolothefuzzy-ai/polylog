# ADR-002: Rendering Stack Selection

**Date:** 2025-10-30  
**Status:** PROPOSED  
**Owners:** Render Team

---

## Context

Polylog needs a stable, deterministic rendering backend that supports:
- Cross-platform deployment (Windows, Linux, macOS)
- Device-lost recovery (<500ms)
- Determinism mode with reproducible frame output
- Custom frame graph + resource management
- Offline shader compilation
- Backwards compatibility via versioned plugin boundary

Four candidates evaluated:

1. **bgfx** — Cross-platform, low-level, mature
2. **Filament** — Modern, PBR-focused, heavier
3. **WGPU** — WebGPU alignment, Rust-based, newer
4. **Direct Vulkan/DX12** — Maximum control, highest maintenance

---

## Evaluation Matrix

| Criterion | bgfx | Filament | WGPU | Direct |
|-----------|------|----------|------|--------|
| **Cross-platform** | ✓✓ | ✓✓ | ✓✓ | ✗ (needs per-API layers) |
| **Device-lost recovery** | ✓ | ✓ | ✓ | ✓✓ (explicit control) |
| **Determinism support** | ✓✓ | ✓ | ✓ | ✓✓ |
| **Maturity / Proven** | ✓✓ (Oculus, AAA) | ✓ (Google, newer) | ✗ (pre-1.0) | ✓✓ (Unreal, Unity) |
| **Material pipeline** | ✗ (minimal) | ✓✓ (great) | ✓ (adequate) | ✓ (custom) |
| **Debugging / profiling** | ✓ | ✓✓ | ✓ | ✓✓ |
| **Community / docs** | ✓✓ | ✓✓ | ✓ | ✓✓ |
| **Build / compile time** | ✓ (fast) | ✗ (slow) | ✗ (slow) | ✗ (slow) |
| **Iteration speed** | ✓✓ (low-level) | ✓ (abstracted) | ✓ (abstracted) | ✓✓ (full control) |
| **Custom frame graph** | ✓✓ (easy) | ✓ (possible) | ✓ (possible) | ✓✓ (trivial) |

---

## Decision

### **SELECTED: bgfx + Custom Frame Graph Layer**

**Rationale:**

1. **Maturity & Production Track Record**
   - Used in Oculus VR, numerous AAA titles
   - Stable API, long maintenance window
   - Proven determinism under fixed dt

2. **Cross-Platform Without Bloat**
   - Single codebase targets D3D11/12, Vulkan, Metal, OpenGL
   - No per-API maintenance burden
   - Smaller binary footprint than Filament

3. **Low-Level Enough for Custom Features**
   - Can implement custom frame graph on top
   - Direct access to command buffers for barrier generation
   - Idempotent resource creation for device-lost recovery

4. **Fast Iteration**
   - Quick shader recompile (DXC pipeline pre-built)
   - Lightweight wrapper for determinism hooks
   - CLI tools for offline PSO generation

5. **Clear Upgrade Path**
   - bgfx behind stable plugin boundary (C ABI)
   - Can swap to WGPU or custom backend in future if needed
   - No hard coupling to rendering implementation

---

## Implementation Plan

### Phase 1: bgfx Integration (Sprint 2, Week 3)
- Add bgfx as CMake external dependency (locked version)
- Wrap bgfx calls in `render::Device` API
- Implement idempotent resource creation/destruction
- Support device-lost injection for testing

### Phase 2: Frame Graph (Sprint 2, Week 4)
- Build DAG compiler on top of bgfx
- Auto-generate barriers between passes
- Track transient allocations
- Implement resource lifecycle management

### Phase 3: Shader Pipeline (Sprint 2, Week 4)
- DXC offline compilation to SPIR-V
- SPIRV-Cross for HLSL → GLSL/MSL
- Cache shader binaries with include-graph hash
- Strict warnings (-Werror) in CI

### Phase 4: Determinism Support (Sprint 3–5)
- Seeded jitter in camera (STAB-017)
- Deterministic PSO cache keys
- Record/replay for GPU state (STAB-034)
- Golden image testing framework (STAB-033)

---

## Trade-Offs

### What We Gain
- ✓ Proven, production-grade stability
- ✓ Cross-platform with low overhead
- ✓ Full control over frame graph and determinism

### What We Sacrifice
- ✗ Built-in material system (must implement custom or use add-on)
- ✗ Less high-level abstraction (more C-style API)
- ✗ Smaller ecosystem vs. Unreal/Unity rendering modules

**Mitigations:**
- Material system can be lightweight add-on (Filament's material description format compatible)
- bgfx C API is well-documented and stable
- Open-source community provides references

---

## Compatibility & Versioning

- **bgfx version:** Locked to `1.x` series; minor updates allowed with CI validation
- **Breaking changes:** Major version bumps only; notify plugin authors 2 releases ahead
- **Fallback rendering:** Unlit path for unsupported features (no breaking visuals)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| bgfx upstream discontinuation | M | Fork if needed; API stable enough to maintain |
| Driver-specific device-lost bugs | M | Chaos testing on Windows/Linux/macOS; known-good matrix |
| Frame graph complexity hidden bugs | M | Extensive unit tests; golden image suite |
| Shader compilation slow spiral | L | Pre-compile all shaders; cache with versioning |

---

## Acceptance Criteria

- ✅ bgfx builds on Windows, Linux, macOS
- ✅ Render triangle with clear color (MVP)
- ✅ Device-lost injection test passes
- ✅ Shader pipeline compiles to SPIR-V with -Werror
- ✅ ADR reviewed and approved by architecture team

---

## References

- https://github.com/bkaradzic/bgfx
- https://bkaradzic.github.io/bgfx/overview.html
- STAB-008 (frame graph)
- STAB-011 (shader toolchain)
- STAB-019 (device-lost)
- STAB-033 (golden images)
