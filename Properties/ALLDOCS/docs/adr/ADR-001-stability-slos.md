# ADR-001: Stability SLOs and Platform Guarantees

**Date:** 2025-10-30  
**Status:** PROPOSED  
**Owners:** Engine Platform Team

---

## Context

The Polylog engine must provide measurable, platform-wide stability guarantees to production applications. Currently, stability is implicit and ad-hoc. We need explicit SLOs (Service Level Objectives) that cover crash-free operation, frame reproducibility, device recovery, API compatibility, and build reproducibility.

---

## Decision

### 1. Crash-Free SLO

**Primary SLO: >99.9% crash-free across all supported platforms**

- **Definition:** User-facing crash-free sessions measured per platform (Windows, Linux, macOS, consoles).
- **Target:** ≤ 1 crash per 1,000 user-sessions
- **Measurement:** Automated telemetry from production deployments
- **Scope:** All subsystems (rendering, physics, audio, IO, scripting)
- **Exclusions:** Developer-triggered assertions (debug builds), customer code crashes

### 2. Frame Reproducibility SLO

**Target: Identical outputs given identical inputs in determinism mode**

- **Definition:** Running the same scene with identical inputs must produce byte-identical render outputs
- **Tolerance:** 0 divergence in determinism mode; ±0.5% frame variance acceptable in variable-dt mode
- **Measurement:** Per-frame hash comparison (physics, culling, GPU dispatch order)
- **Scope:** Single-player, offline, replay scenarios
- **Triggers:** Determinism mode enabled by default in tests; optional runtime toggle

### 3. Device-Loss Recovery SLO

**Target: <500ms recovery time on device-lost events**

- **Definition:** GPU reset/crash → idempotent resource teardown → successful recreation
- **Tolerance:** <500ms visible freeze
- **Measurement:** Synthetic chaos tests on per-driver basis
- **Scope:** Windows (DXGI), Linux (Vulkan), macOS (Metal)
- **Success:** Render resumes, no handle leaks, user state preserved

### 4. API/ABI Stability Windows

**Semantic Versioning + Compatibility Guarantees**

- **Format:** MAJOR.MINOR.PATCH (e.g., 1.2.3)
- **Deprecation:** 2 minor release windows before removal (breaking changes deferred to MAJOR bumps)
- **ABI Forward-Compatibility:** 1 version minimum; plugins built on v1.2 must load on v1.3
- **C Plugin Boundary:** Versioned ABI with capability negotiation (see STAB-009)
  - Plugin version query: `engine_get_version()` → (major, minor)
  - Capability bits: render features, physics version, asset format support
  - Mismatch handling: Graceful disable or error message, never silent corruption

### 5. Reproducible Builds Policy

**Target: Byte-for-byte identical binaries across machines**

- **Definition:** Same source, same locked toolchain versions → identical output
- **Scope:** Release builds (optimized, symbol stripping varies per platform)
- **Locked Dependencies:**
  - C++ compiler versions (MSVC, Clang, GCC via version pins)
  - SDK versions (Windows SDK, Android NDK, console SDKs)
  - Third-party library versions (via conanfile.lock, vcpkg.lock, or git submodule pins)
  - Shader compiler (DXC, SPIRV-Cross versions frozen)
- **Validation:** Automated CI step on each release: build twice, diff binaries
- **Non-deterministic sources allowed:**
  - Timestamps in binaries (stripped before comparison)
  - Debug symbol tables (optional comparison)
  - RTTI tables (if link-order stable)

---

## Implications

### Code Level

1. **All randomness must be seeded in determinism mode** (STAB-006)
   - Physics RNG, particle generators, audio dithering all controlled by seed
   - `core::DeterminismMode::IsEnabled()` check before any non-deterministic operation
   - Default seed = 42 for reproducible tests

2. **Physics, rendering, and asset loading must be deterministic**
   - Fixed-step solver (STAB-005, STAB-030)
   - Sorted island processing (STAB-032)
   - Deterministic asset import (STAB-025)
   - Frame graph with explicit barriers (STAB-008)

3. **No runtime shader compilation in production** (STAB-011, STAB-055)
   - Shaders compiled offline to IR (SPIR-V)
   - Signed blobs checked at load time
   - Fallback materials for unsupported features

4. **Crash reporting captures full context** (STAB-040, STAB-041)
   - Scene hash, driver version, GPU capabilities
   - Random seeds, input history, callstack with symbols
   - Repro packs enable one-click reproduction (STAB-041)

### Operational Level

1. **SLO dashboards and alerting** (STAB-039, STAB-051)
   - Real-time KPI tracking per platform
   - Regression alerts on perf/stability metrics
   - Crash bucketing and triage automation

2. **Quarterly driver/toolchain validation** (STAB-050)
   - Known-good matrix published per release
   - Driver version ranges, SDK versions, console firmware
   - Blockers on unsupported configurations

3. **Release gates enforced** (STAB-057)
   - No production build without passing:
     - Device-loss chaos test (10 cycles)
     - 24h soak with leak tracking
     - Determinism suite (3 identical runs)
     - Golden image regressions (<5% SSIM delta)
     - Pipeline rebuild verification

---

## Acceptance Criteria

- ✅ ADR reviewed and approved by engine leads
- ✅ SLO targets entered into project management system
- ✅ Determinism mode plumbed to all subsystems (Sprint 2–5)
- ✅ Crash reporting telemetry infrastructure in place (Sprint 3)
- ✅ Release gates automated and passing (Sprint 6)

---

## Notes

- Initial rollout focuses on desktop (Windows, Linux, macOS)
- Console SLOs may differ per platform; handled in child ADRs
- Crash-free target may be tightened to >99.95% post-launch based on telemetry

---

## References

- STAB-001 (this ADR)
- STAB-005, STAB-006 (determinism infrastructure)
- STAB-025, STAB-030, STAB-032 (deterministic systems)
- STAB-039, STAB-051 (observability)
- STAB-057 (acceptance gates)
