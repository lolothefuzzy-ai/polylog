# Polylog6

Polylog6 is an experimental polyform simulation and compression toolkit.

## Quick Status

**Current Phase:** Phase 2 (Frontend Integration - Ready to Start)
**Status:** Ready to Execute | **Blockers:** None

**Check Status First:** See `EXECUTION_READY.md` for current system status and next steps.

## Documentation

### Active Status (Check These First)
- **EXECUTION_READY.md** - Current phase, blockers, next actions
- **OPTIMIZED_PHASE_2_PLAN.md** - Phase 2 implementation details

### Reference Architecture (For Understanding)
- **PROJECT_SCOPE_AND_BLOCKERS.md** - Project scope and 10 identified blockers
- **IMPLEMENTATION_ROADMAP.md** - 6-phase roadmap with timelines
- **EDGE_FACE_MATCHING_ARCHITECTURE.md** - Geometric validation architecture
- **SYSTEM_OPTIMIZATION_ANALYSIS.md** - System optimization strategy

### Legacy Documentation
- **PolylogStructure and Science/integration_architecture/** - Original architecture docs

## Core Workflows

### Storage Compression Metrics (INT-002/005)

Generate and summarize telemetry artifacts in one step:

```bash
python scripts/run_compression_metrics.py --label=dev --output=metrics.json
```

This command executes `test_storage_pipeline.py`, captures the pytest JSON
report, and writes a consolidated `metrics.json` for ingestion by the telemetry
dashboard. Use `--keep-report` to retain the intermediate pytest artifact. The
CI pipeline runs this command automatically and uploads `compression_metrics.json`
artifacts for every build, so downstream dashboards always consume the latest
ratios. Re-run locally whenever updating storage logic so the pipeline stays in
sync with `integration_architecture/roadmap/polylog_development_status.md`.

### Registry Parity Monitoring (INT-006)

```python
from polylog6.monitoring.alerts import ListAlertSink
from polylog6.monitoring.registry_reconciliation import RegistryReconciliationHarness

sink = ListAlertSink()
harness = RegistryReconciliationHarness(storage_manager, sinks=[sink])
baseline = harness.capture_snapshot("baseline")
parity, diff = harness.verify_parity(baseline)
```

Attach one or more alert sinks (e.g., `ListAlertSink`, `LoggingAlertSink`) when
instantiating the reconciliation harness. Any parity drift emits actionable
alerts, which CI and local monitoring can surface without additional wiring.

### Catalog Scaffold (Optional for hydrator development)

```bash
python scripts/run_catalog_generators.py
python -m pytest tests/test_catalog_generators.py
```

The generators emit placeholder catalogs under `catalogs/`; replace them with
production data as INT-009 catalog population advances.

### Geometry Backends (INT-014)

`integration_architecture/README.md` now documents the default Trimesh/SciPy
stack plus optional CGAL acceleration. Install helpers:

```bash
# default desktop bundle
pip install trimesh scipy numpy shapely

# optional CGAL acceleration via conda
conda install -c conda-forge scikit-geometry trimesh scipy numpy shapely
```

## Test Suite

```bash
python -m pytest
```

Individual modules expose targeted suites under `tests/` and
`src/polylog6/*/tests/` for faster iteration.
