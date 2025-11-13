# Polylog Integration Architecture Hub

All current documentation is organized here for quick ingestion by external
research models or collaborators. Use the sections below to jump directly to the
latest sources of truth.

## Directory Map

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `roadmap/` | Current delivery priorities, execution sequencing, progress snapshots. | [`polylog_development_status.md`](roadmap/polylog_development_status.md) |
| `tickets/` | Integration backlog with ownership and dependency tracking. | [`integration_ticket_backlog.md`](tickets/integration_ticket_backlog.md) |
| `architecture/` | Core system specifications for compression, dictionary, simulator, and hybrid topology efforts. | `POLYFORM_COMPRESSION_ARCHITECTURE.md`, `POLYFORM_DICTIONARY_SYSTEM.md`, `POLYFORM_SIMULATOR_COMPREHENSIVE_SPEC.md`, `polyform_backbone_architecture.md`, `POLYFORM_SIMULATOR_SPEC.docx` |
| `design/` | Work-in-progress design notes (catalog generation, engine requirements, structure/science synthesis). | `catalog_generation_roundup.md`, `engine_functionality_requirements.md`, `structure_science_synthesis.md` |
| `research/` | Active research alignment docs. | `research_implementation_mapping.md`, `polyform_simulator_architecture_research.md`, `unicode_symbol_allocation_strategy.md`, `visualization_performance_optimization.md` |
| `reference/` | Supporting PDFs, legacy briefs, and historical snapshots. | `polyform_storage_and_encoding.pdf`, `legacy/DEVELOPMENT_STATUS_AND_ROADMAP.md` |

## Detection API (INT-014)

- FastAPI router exposed via `polylog6.detection.router`.
- Endpoints:
  - `POST /detection/analyze` → returns synchronous detection plan payload.
  - `POST /detection/analyze_async` → schedules background analysis (callback wiring pending).
  - `POST /detection/telemetry` → accepts telemetry with schema version `0.1`.
  - Refer to `polylog6/detection/ipc.py` for payload schemas shared with the Tauri client.
- Telemetry carries `topology_backend`, per-region hull summaries, and rollup metrics (`hull_region_count`, `hull_volume_total`, `avg_candidate_score`). Consumers should expect hull metadata on each candidate entry.
- Candidate scoring now blends descriptor strength with hull-derived metrics (compactness, density, thickness). Runtime guardrail test enforces <0.5s execution for stub pipeline.
- Geometry backends:
  - Default (pip): Trimesh + SciPy (bundled with desktop build).
  - Optional performance mode (conda): `scikit-geometry` (CGAL) auto-detected when installed; see `polylog6/detection/topology.py`.
  - Installation quick-start:
    - **pip (default desktop bundle)**

      ```bash
      pip install trimesh scipy numpy shapely
      ```

    - **conda (enables scikit-geometry acceleration)**

      ```bash
      conda install -c conda-forge scikit-geometry trimesh scipy numpy shapely
      ```

- Catalog population:
  - Run `python scripts/populate_catalogs.py` once `stable_polyforms.jsonl` lands to emit `catalogs/attachment_graph.json` and `catalogs/scaler_tables.json`.
  - Outputs feed INT-010+ placement runtime tasks; rerun whenever production polyform data changes.
- Monitoring kickoff:
  - `ContextBriefTailer` + `LibraryRefreshWorker` now available under `polylog6.monitoring`.
  - Integration plan: wire `LibraryRefreshWorker.watch()` into the async coordination loop (INT-003), binding alert sinks before enabling refresh callbacks (INT-004).
  - `dispatch_once` helper bridges tailer output to refresh worker and detection telemetry; pair with `DetectionTelemetryBridge` to surface hull metrics in dashboards.
  - `MonitoringLoop` wraps the dispatcher with feature-flag gating and poll interval config for production runtime integration.
- Detection bring-up (Phase 1):
  - `scripts/validate_detection_input.py` validates real image assets and generates synthetic fixtures under `tests/fixtures/images/`.
  - `scripts/test_detection_real_image.py` runs the full detection pipeline on the curated fixtures, emitting segmentation overlays and telemetry logs.
  - Refer to `integration_architecture/research/detection_monitoring_research.md` for the Phase 1→3 research roadmap (segmentation calibration, topology backends, telemetry wiring).
- Upcoming calibration (Phase 2):
  - Capture Felzenszwalb sweeps via `scripts/calibrate_segmentation.py`, persist baselines to `tests/fixtures/expected_segmentations.json`.
  - Add regression coverage (`tests/test_segmentation_regression.py`, `tests/test_pattern_analysis_real.py`) once calibration artifacts exist.
  - Use `scripts/tune_pattern_thresholds.py` to derive symmetry/FFT heuristics; update `tests/fixtures/expected_patterns.json` accordingly.
- Monitoring integration (Phase 3):
  - Wire detection telemetry through `MonitoringLoop` into dashboards, align alert thresholds with research guide recommendations.
- CI gating:
  - `storage-regression.yml` enforces INT-002 compression thresholds (Tier1 ≥85 %, Tier2 ≥65 %) and publishes `compression_metrics.json` artifacts on every push/PR.

## Catalog & Monitoring Utilities

- **Catalog hydration:**
  - `scripts/validate_polyform_schema.py` verifies `stable_polyforms.jsonl` against the expected schema prior to INT-009 runs.
  - `scripts/populate_catalogs.py` now emits artifact checksums (`catalogs/metadata.json`) and supports multiprocessing pre-processing.
- **Monitoring support:**
  - `config/monitoring.yaml` drives `polylog6.monitoring.config.load_monitoring_settings()` for feature flags and path discovery.
  - `ContextBriefWatcher` (watchdog-backed) delivers rotation-aware ingestion for `ContextBriefTailer`.
  - `polylog6.monitoring.digest.compute_registry_digest()` provides deterministic parity hashes with `tests/test_monitoring_digest.py` coverage.

## Usage Guidance

1. **Status Updates:** Consume `roadmap/` first to understand current milestones,
   blockers, and sequencing before diving into architectural detail.
2. **Ticket Sync:** `tickets/` mirrors the live backlog; update ownership or
   status here to keep integration planning consistent across agents.
3. **Architecture Deep Dive:** Leverage `architecture/` for spec-level detail on
   compression, Unicode integration, CGAL hybrid design, and simulator wiring.
4. **Design Notes:** Files under `design/` capture evolving procedures (catalog
   generation, guardrail workflows) that support implementation tracks.
   - Monitoring & alert playbook lives in [`design/structure_science_synthesis.md`](design/structure_science_synthesis.md#monitoring-sop-int-006)
     and documents baseline capture, alert sink wiring, and remediation steps.
5. **Research Coordination:** Use `research/` when syncing with external
   research models; place new briefs here to keep the hub discoverable.
6. **Legacy References:** Anything superseded but still historically useful lives
   under `reference/`. Avoid editing legacy docs; promote new content into the
   active directories instead.

## Contribution Checklist

- Update roadmap and ticket documents in tandem to keep the execution view
  consistent.
- Prefer linking between files using relative paths inside this directory to
  simplify downstream consumption.
- When retiring docs, move them into `reference/legacy/` rather than deleting so
  historical context remains available.
- Regenerate telemetry or metrics artifacts before publishing updates to ensure
  the documentation reflects current baselines.
