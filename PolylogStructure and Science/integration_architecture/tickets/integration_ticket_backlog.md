# Integration Ticket Backlog

## Purpose

Track integration-sized work items required to operationalize the Unicode compression pipeline and two-agent workflow. Each ticket is scoped for asynchronous execution and can be mirrored in the coordination inbox for live status.

## Tickets

| ID | Title | Owner | Priority | Status | Dependencies | Description |
|----|-------|-------|----------|--------|--------------|-------------|
| INT-001 | Rehydrate engine package & checkpoint loop | Agent G | Critical | Complete | Workspace streaming scaffold | Shim exports, `SimulationEngine`, and `GeometryRuntime` restored; checkpoint API validated via smoke tests and storage round-trips. |
| INT-002 | Automated chunk streaming regression harness | Agent G | High | Complete | INT-001 | `storage-regression.yml` workflow enforcing Tier1 ≥85 % / Tier2 ≥65 % merged; pytest JSON reporting + baseline (2025-11-09) recorded for CI alerts. |
| INT-003 | Async inbox watcher & notifier | Agent C | High | In Progress | INT-001 | Config loader + watcher helper landed; integrate watcher with async coordination loop, add dispatcher wiring, and produce runbook telemetry sample. |
| INT-004 | Context library reindex from streamed chunks | Agent C | High | In Progress | INT-003 | Registry drift e2e test + runbook landed; next wire telemetry latency (<100 ms) and finish refresh parity gating. |
| INT-005 | Compression telemetry dashboard | Joint | Medium | Complete | INT-002 | Dashboard scaffold and telemetry pipeline wired into CI (`compression_metrics.json` artifacts) with operator documentation underway. |
| INT-006 | Symbol registry snapshot reconciliation | Agent C | Medium | Complete | INT-002 | Harness emits alerts through monitoring sinks; parity remediation path documented and covered by regression tests. |
| INT-007 | Stability overflow guardrails in engine loop | Agent G | High | Complete | INT-001 | Dimension-aware guardrails merged; regression suite green. |
| INT-008 | Documentation + SOP updates | Joint | Low | In Progress | INT-001–INT-007 | Updated design synthesis with telemetry/alert procedures; finalize guardrail and catalog SOP integrations next. |
| INT-009 | Catalog generation & hydrator prep | Agent G | Medium | In Progress | INT-001 | Multiprocessing CLI emits attachment/scaler artifacts + metadata checksums; hydration benchmarks captured (serial vs parallel) and tracked in pattern_tuning benchmarks log. |
| INT-010 | Placement runtime attachment resolver | Agent G | High | In Progress | INT-009 | Context-aware resolver implemented + wired into placement runtime with auto schema selection; finalize catalog hydration + scoring heuristics. |
| INT-011 | Cascading combinatorial calculator integration | Agent G | High | Planned | INT-009 | Implement O/I memoization seeded from scaler tables and surface metrics post-placement. |
| INT-012 | Instant fold sequencer & collision validation | Agent G | High | Planned | INT-009 | Implement catalog-driven fold sequencer with BVH collision checks and integrate metadata return path. |
| INT-013 | CGAL + Unicode hybrid topology cache | Agent G | Medium | Planned | INT-002, INT-009 | Integrate CGAL detector fingerprinting with Unicode schema matrix, add HybridTopologyResolver, and extend regression metrics for detection vs lookup performance. |
| INT-014 | Detection-first image analysis pipeline | Agent G (Track A) | High | In Progress | INT-002, INT-005 | Phase 2 calibration/regression complete (`calibrate_segmentation.py`, pattern tests); next: symmetry tuning + monitoring wiring with updated telemetry bridge. |

## Optimized Near-Term Focus

### Path A – Main Integration

1. **INT-002** – Finalize regression harness metrics and wire into CI gates.  
2. **INT-003 / INT-004** – Stand up monitoring loop and context library refresh in tandem.  
3. **INT-010 / INT-011 / INT-012** – Deliver placement runtime integration stack (attachment resolver, combinatorial calculator, fold sequencer) on top of populated catalogs.  
4. **INT-009** – Complete production catalog population to unblock hydrator swap-in.
5. **Track A Sprint (INT-014) – Real Image Detection**  
   - Phase 1: ensure dependencies (`opencv-python`, `scikit-image`, `trimesh`) installed; run `python scripts/validate_detection_input.py` and `python scripts/test_detection_real_image.py`.  
   - Phase 2: execute `python scripts/calibrate_segmentation.py`, commit `tests/fixtures/expected_segmentations.json`, and run `pytest tests/test_segmentation_regression.py`.  
   - Phase 3: populate `tests/fixtures/expected_patterns.json`, run `pytest tests/test_pattern_analysis_real.py`, and feed telemetry through `MonitoringLoop`.  
   - Reference `integration_architecture/research/detection_monitoring_research.md` for design rationale and thresholds.

### Path B – Easy Wins (Updated)

1. **INT-005 – Telemetry publishing polish**  
   - Ship CI job that runs `parse_metrics.py` and uploads `compression_metrics.json`.  
   - Add operator README snippet describing dashboard usage and alert thresholds.
2. **INT-006 – Harness wiring**  
   - Connect reconciliation harness outputs to monitoring alerts + registry replay trigger.  
   - Highlight alert workflow reference: [`structure_science_synthesis.md`](../design/structure_science_synthesis.md#monitoring-sop-int-006) for baseline capture, alert routing, and remediation steps.  
   - Capture SOP covering snapshot capture, diff triage, and rollback.
3. **INT-008 – Documentation refresh**  
   - Fold new guardrail + catalog procedures into SOPs.  
   - Reference newly published Unicode compression + CGAL briefs where relevant.
4. **INT-003 – Monitoring dispatcher integration**  
   - Embed `MonitoringLoop` (feature-flag aware) into the async coordination service.  
   - Register alert sinks and smoke-test digest ingestion → refresh trigger → alert emission.
5. **INT-004 – Automated refresh validation**  
   - Execute end-to-end mismatch scenario; document runbook and telemetry outputs.  
   - Surface refresh counts and alert codes in monitoring dashboard.
6. **INT-009 – Catalog hydration (follow-on)**  
   - Run `python scripts/populate_catalogs.py` with current `stable_polyforms.jsonl`; diff outputs and update fixtures.  
   - Document rerun cadence and checksum verification.
7. **INT-010 – Placement resolver prep**  
   - Feed refreshed catalogs into resolver stubs and add fixture-driven tests.  
   - Publish dependency map for INT-011/012 follow-up.
8. **INT-002 – CI observability enhancements**  
   - Extend `storage-regression.yml` artifacts with chunk fill histograms and detection telemetry alerts.  
   - Update operator dashboard change log.

### Visualization Optimization (New)

| ID | Title | Owner | Priority | Status | Dependencies | Description |
|----|-------|-------|----------|--------|--------------|-------------|
| VIZ-001 | GPU instancing for repeated polyforms | Track A Visualization | Critical | Planned | INT-014 Phase 2 fixtures | Detect identical sub-assemblies and render via `InstancedMesh` to cut draw calls ≥50×; instrument logging for instancing coverage. |
| VIZ-002 | Catalog-driven LOD pipeline | Track A Visualization | Critical | Planned | VIZ-001, INT-009 catalogs | Generate 3-level LOD meshes during catalog population, persist in `lod_metadata.json`, and consume with `THREE.LOD` thresholds (5 / 20 units). |
| VIZ-003 | Progressive geometry loader | Track A Visualization | High | Planned | VIZ-002 | Implement AABB-first render (<50 ms) with async full-geometry upgrade (<90 ms); integrate with React Three Fiber scene manager. |
| VIZ-004 | Interaction & selection framework | Track A Visualization | High | Planned | VIZ-003 | Wire R3F pointer events for click/context menu, manage selection via Zustand, and integrate `react-contexify` menus with sub-100 ms response. |
| VIZ-005 | Worker offload for heavy geometry ops | Track A Visualization | High | Planned | VIZ-003 | Move topology/LOD preprocessing to Web Workers using Comlink to keep main thread frames <16 ms. |
| VIZ-006 | Memory monitoring & disposal hooks | Track A Visualization | Medium | Planned | VIZ-002 | Add `stats.js` budget monitor (200 MB cap) and `useDisposableGeometry` hook to prevent leaks on LOD swap/removal. |
| VIZ-007 | Tauri IPC geometry bridge | Track B Integration | Medium | Planned | INT-005 telemetry, INT-009 catalogs | Replace HTTP fetches with Tauri commands for catalog data, targeting 10× latency reduction; keep FastAPI for heavy compute only. |
| VIZ-008 | Performance regression harness | Track A Visualization | Medium | Planned | VIZ-001–VIZ-006 | Add Puppeteer FPS test (≥30 FPS @ 1k polyforms) and Storybook image snapshots for visual regressions. |
| VIZ-009 | Stress & memory validation suite | Track A Visualization | Low | Planned | VIZ-008 | Automate 5k-polyform stress run, capture heap snapshots, and document maximum supported complexity with fallback strategy. |
