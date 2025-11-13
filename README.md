# Polylog6

Polylog6 is an experimental polyform simulation and compression toolkit.

## Documentation Hub

All integration, roadmap, architecture, and research notes now live under:

```text
PolylogStructure and Science/integration_architecture/
```

Key entry points:

- `roadmap/` – current delivery priorities and status.
- `tickets/` – integration backlog (Path A/B, dependencies, owners).
- `architecture/` – compression, dictionary, simulator, and backbone specs.
- `design/` – catalog generation, engine requirements, structure/science synthesis.
- `reference/` – legacy briefs and reference PDFs.

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
