# Polyform Simulator Architecture Research

**Date:** 2025-11-08  
**Status:** Pre-implementation strategy phase  
**Purpose:** Provide research-driven architectural recommendations for a stable, production-ready one-click desktop polyform simulator. Focus on system design patterns, performance budgets, and deployment pathways rather than implementation details.

---

## Executive Summary

### Project Vision

- One-click desktop application for generating, visualizing, and analyzing 3D polyform assemblies.
- Target capabilities:

  - Real-time 3D visualization with sub-100 ms interaction latency.
  - Automated assembly generation across six expansion patterns (Explore, Stable Iteration, Linear, Cubic, Explosive, Radial).
  - Mathematical precision: O/I combinatorial metrics validated against ground truth.
  - Memory efficiency via cascading reference architecture, capped at ~500 MB.
  - Cross-platform deployment (Windows, macOS, Linux).

### Current State (Nov 2025)

- ✅ Unicode compression architecture (85–95% storage reduction) delivered.
- ✅ Guardrail integration (dimension-aware stability checks) validated in SimulationEngine.
- ✅ Storage regression harness (INT-002) with mega-scale fixtures operational.
- ✅ Catalog scaffolding for geometry, attachment, scaler, and LOD generators available for population.
- 🔄 INT-002 metrics baseline (compression ratio telemetry) under active development.
- 🔄 INT-005 Unicode library prepopulation (Tier 0–2) in progress.
- 🔄 Catalog population with production-grade data launched.
- 🔄 CGAL + Unicode hybrid topology detection planned.
- Gaps: attachment resolver, combinatorial cascading calculator, instant fold sequencer, desktop UI technology decision.

### Strategy Themes

- Hybrid detection (CGAL + Unicode) for accuracy + performance.
- Tiered Unicode storage architecture for high hit rates and memory predictability.
- Streamed visualization with progressive enhancement (AABB-first).
- Cascading references and combinatorial memoization to meet memory/latency budgets.
- Tauri-led desktop distribution for fast installs and low footprint (evaluate PyQt6 for native migrations).

---
