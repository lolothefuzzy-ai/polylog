# Polyform Detection & Monitoring Architecture Image Brief

**Audience:** External research model contributors

**Purpose:** Provide a single-page visual reference that explains how the detection-first pipeline (Track A) and monitoring loop (Track B) interlock. The diagram should highlight major subsystems, data artifacts, control flow, and telemetry touchpoints required for collaborative development.

---

## 1. Diagram Goals

1. Convey system layers from raw imagery ingestion to monitoring dashboards.
2. Show the runtime split between desktop (local pipeline) and cloud/shared services.
3. Emphasize feature flags, telemetry emission, and feedback loops that research partners must respect.
4. Embed key artifacts (fixtures, baselines, catalogs) to anchor collaboration tasks.
5. Provide canonical color palette + iconography to keep derivative diagrams consistent.

---

## 2. Recommended Layout

```text
+-----------------------------------------------------------------------------------+
|                                Layer 0 – Inputs                                   |
|  • Real imagery (fixtures, captured assets)                                        |
|  • Synthetic baselines (calibration overlays)                                      |
+-----------------------------------------------------------------------------------+
|                                Layer 1 – Detection                                |
|  ImageSegmenter  →  PatternAnalyzer  →  TopologyDetector  →  CandidateOptimizer    |
|  | Felzenszwalb + K-means |   | FFT + symmetry |   | CGAL/Trimesh |   | NSGA-lite |
|  Outputs: segmented regions, descriptors, hull summaries, candidate plans          |
+-----------------------------------------------------------------------------------+
|                                Layer 2 – Telemetry                                |
|  DetectionTelemetryBridge  →  MonitoringLoop / Dispatcher →  ContextBriefTailer    |
|  Metrics: region counts, coverage %, hull stats, compression ratios                |
+-----------------------------------------------------------------------------------+
|                                Layer 3 – Monitoring                               |
|  LibraryRefreshWorker  →  Catalogs/Registry  →  Dashboards & Alerts                |
|  Feature gates: detection.enabled, telemetry.enabled, refresh.enabled              |
+-----------------------------------------------------------------------------------+
```

- **Swimlanes:** Use horizontal swimlanes to distinguish runtime environments:
  - *Left column:* Desktop runtime (scripts and tests).
  - *Center:* Polylog6 services (FastAPI, monitoring dispatcher).
  - *Right column:* Observability/operations (dashboards, runbooks).

- **Color coding:**
  - Detection components → teal (#0B7285)
  - Monitoring components → indigo (#364FC7)
  - Data artifacts (fixtures, catalogs) → orange (#F59F00)
  - External integrations (dashboards, research feedback) → gray (#495057)

---

## 3. Callouts & Annotations

Label the following anchors on the diagram and link to repository paths:

| Anchor | Description | Repo Reference |
|--------|-------------|----------------|
| A | Real image fixtures and calibration outputs | `tests/fixtures/images/`, `tests/fixtures/segmentation_snapshots/` |
| B | Calibration & regression scripts | `scripts/calibrate_segmentation.py`, `tests/test_segmentation_regression.py` |
| C | Detection service entrypoints | `src/polylog6/detection/service.py`, `scripts/test_detection_real_image.py` |
| D | Telemetry emission contract | `src/polylog6/detection/service.py::ImageDetectionService.emit_telemetry`, `monitoring/dispatcher` |
| E | Monitoring dispatcher + tailer | `src/polylog6/monitoring/dispatcher.py`, `monitoring/loop.py` |
| F | Dashboard & runbook references | `PolylogStructure and Science/integration_architecture/research/detection_monitoring_research.md`, `.../README.md` |

Include text balloons for:
- **Feature flags:** `detection.enabled`, `telemetry.enabled`, `refresh.enabled` (show gating points).
- **Telemetry schema:** `schema_version = 0.1` with metrics list (region_count, candidate_count, coverage%).
- **Feedback loop:** arrow from dashboards/runbooks back to detection calibration tasks.

---

## 4. Deliverables for External Model

1. **Vector diagram (SVG preferred)**
   - Export at 2560×1440 for presentations.
   - Include layered groups so future updates can toggle Track A/Track B elements.
2. **Thumbnail PNG** (800×450) for quick embedding in READMEs.
3. **Callout legend** describing palette, iconography, and anchor labels (can be placed beneath diagram).
4. **Update instructions** specifying how to modify the diagram when new telemetry signals or detection stages are added.

---

## 5. Suggested Tooling

- Figma or Excalidraw with shared library of Polylog6 icons.
- Alternatively, Mermaid + manual SVG refinement for lightweight iteration.
- Store source (`.fig`, `.excalidraw`, or `.mmd`) under `integration_architecture/diagrams/` and export artifacts under `integration_architecture/assets/`.

---

## 6. Handoff Checklist

- [ ] Diagram reviewed by Track A and Track B leads for accuracy.
- [ ] Palette and callouts validated against documentation.
- [ ] Source + exports committed alongside this brief.
- [ ] Link added to integration architecture README under “Architecture Images”.

---

**Last updated:** 2025‑11‑09  
**Maintainer:** Track A Detection (primary), Track B Monitoring (secondary)
