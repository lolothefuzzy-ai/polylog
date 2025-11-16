# Polyform Detection & Monitoring Research Guide

**Purpose:** Consolidate conceptual references, architectural patterns, and best practices for integrating real-world image detection with the Polylog6 simulation and monitoring stack. Emphasis is on the “why” and “what”; implementation details remain in source files.

---

## 1. Image Segmentation & Region Detection

### 1.1 Graph-Based Segmentation (Felzenszwalb)

- **Paper:** [Efficient Graph-Based Image Segmentation](http://people.cs.uchicago.edu/~pff/papers/seg-ijcv.pdf) — Felzenszwalb & Huttenlocher (2004).
- **Why it matters:** Boundary-preserving over-segmentation with only three tunables (`scale`, `sigma`, `min_size`), ideal for downstream topology.
- **Operational guidance:**
  - Prefer `skimage.segmentation.felzenszwalb` when available; tune `scale` in the 50–400 range for our fixtures.
  - Retain K-means + connected components as the CPU-only fallback.
- **Further reading:**
  - [scikit-image API reference](https://scikit-image.org/docs/stable/api/skimage.segmentation.html#skimage.segmentation.felzenszwalb)
  - [Segmentation comparison gallery](https://scikit-image.org/docs/stable/auto_examples/segmentation/plot_segmentations.html)

### 1.2 Semantic Segmentation Alternatives

- **SAM (Segment Anything Model):** [Segment Anything](https://arxiv.org/abs/2304.02643) — overkill for now but useful as a future “advanced mode.”
- **Watershed + Canny (OpenCV):** [Tutorial](https://docs.opencv.org/4.x/d3/db4/tutorial_py_watershed.html) — deterministic CPU pipeline for splitting merged regions when Felzenszwalb under-segments.

---

## 2. Computational Geometry for Topology Detection

### 2.1 Convex Hull Algorithms

- **Paper:** [The Quickhull Algorithm for Convex Hulls](https://dl.acm.org/doi/10.1145/235815.235821) — Barber et al. (1996).
- **Pipeline:** segmented vertices → `scipy.spatial.ConvexHull` → volume/area/face metrics → topology fingerprints.

### 2.2 CGAL vs. Pure Python Backends

- **CGAL overview:** <https://www.cgal.org/>
- **Bindings:**
  - `trimesh` (pip) — default, portable.
  - `scikit-geometry` (conda) — CGAL precision, boolean ops.
  - `pyvista` (pip) — visualization-heavy workflows.
- **Decision:** Ship with `trimesh`; enable CGAL-backed paths for high-precision deployments. [Intro article](https://wolfv.medium.com/introducing-scikit-geometry-ae1dccaad5fd).

### 2.3 Collision Detection & BVH

- **Paper:** [Fast Collision Detection for Deformable Models Using Representative-Triangles](https://gamma.cs.unc.edu/RT/) — Sud et al. (2004).
- **Project tie-in:** `src/polylog6/bvh3d.py` already offers broad-phase culling; integrate before hull calculations.

---

## 3. Pattern Recognition & Symmetry Detection

### 3.1 FFT-Based Periodicity

- **References:** [NumPy FFT docs](https://numpy.org/doc/stable/reference/routines.fft.html), [SciPy peak detection](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html).
- **Use case:** Identify repeating motifs and lattice-like arrangements; tune thresholds via calibration fixtures.

### 3.2 Symmetry Group Detection

- **Paper:** [Symmetry Detection by Generalized Circular Projection](https://www.cv-foundation.org/openaccess/content_cvpr_2006/papers/Cornelius_Symmetry_Detection_by_CVPR06.pdf) — Cornelius & Loy (2006).
- **Application:** Score bonuses for cyclic/dihedral symmetries; feed into topology validation.
- **Primer:** [mathopenref symmetry explorer](https://www.mathopenref.com/symmetry.html).

---

## 4. Candidate Scoring & Optimization

### 4.1 Multi-Objective Optimization

- **Paper:** [NSGA-II](https://ieeexplore.ieee.org/document/996017) — Deb et al. (2002).
- **Guidance:** Maintain weighted-sum scoring for now; consider Pareto analysis when UI needs multi-criteria controls.

### 4.2 Bayesian Hyperparameter Tuning

- **Tool:** [Optuna docs](https://optuna.readthedocs.io/en/stable/).
- **Paper:** [Optuna: Next-generation Hyperparameter Optimization](https://arxiv.org/abs/1907.10902) — Akiba et al. (2019).
- **Targets:** Segmentation params, scoring weights, FFT/symmetry thresholds. Reuse `optuna_placement_tuner.py` patterns.

### 4.3 Compression Ratio as Quality Metric

- **Paper:** [Adaptive Arithmetic Coding](https://dl.acm.org/doi/10.1145/214762.214771) — Witten et al. (1987).
- **Usage:** Cross-reference results with `scaler_tables.json` to measure catalog compression efficiency; alert when below Tier thresholds (85 % / 65 %).
- **See also:** `POLYFORM_COMPRESSION_ARCHITECTURE.md`.

---

## 5. Real-Time Detection Pipeline Design

### 5.1 Processing Modes

- **Paper:** [The Dataflow Model](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/43864.pdf).
- **Patterns:** synchronous UI requests, async task queues (Celery), streaming feeds (FastAPI background tasks + asyncio).

### 5.2 Memory Management

- **References:** [OpenCV intro](https://docs.opencv.org/4.x/d1/dfb/intro.html), [Netflix encoding blog](https://netflixtechblog.com/per-title-encode-optimization-7e99442b62a2).
- **Practices:** tile 4K+ images, downsample with `INTER_AREA`, stream large files with `numpy.memmap`.

---

## 6. Monitoring & Telemetry Integration

### 6.1 Observability

- **OpenTelemetry:** <https://opentelemetry.io/> and [Python instrumentation](https://opentelemetry.io/docs/instrumentation/python/).
- **Roadmap:** Wrap existing telemetry callbacks with OT spans/metrics; export to Prometheus or similar.

### 6.2 Alert Threshold Tuning

- **Paper:** [Robust Threshold Selection for Time Series Anomaly Detection](https://arxiv.org/abs/1704.07706).
- **Examples:** detection duration >30 s, zero regions, low compression ratio, hull failures. Combine static targets with percentile-based baselines.
- **Case study:** [Netflix adaptive alerting](https://netflixtechblog.com/scryer-netflixs-predictive-auto-scaling-engine-a3f8fc922270).

### 6.3 Context-Aware Monitoring

- **Pattern:** [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html).
- **Architecture:** detection emits context brief JSONL → `ContextBriefTailer` → `MonitoringLoop` → `LibraryRefreshWorker` → dashboards & alerts.

---

## 7. Cross-Platform Dependency Management

### 7.1 Conda vs. Pip

- **Resources:** [Conda docs](https://docs.conda.io/en/latest/), [Understanding Conda & Pip](https://www.anaconda.com/blog/understanding-conda-and-pip).
- **Strategy:** pip for mainstream wheels (OpenCV, Trimesh, SciPy); conda env for CGAL-backed `scikit-geometry` when required.

### 7.2 Packaging Considerations

- **PyInstaller:** <https://pyinstaller.org/>, [OpenCV recipe](https://github.com/pyinstaller/pyinstaller/wiki/Recipe-OpenCV).
- **Challenges:** hidden imports (`cv2`, `skimage.filters`), bundling NumPy/SciPy DLLs, shipping fixture/config data.

---

## 8. Testing Strategies

### 8.1 Fixture Management

- Generate deterministic fixtures (triangles, grids, noisy backgrounds) via `scripts/validate_detection_input.py`.
- Mirror scikit-image’s data layout for images, metadata, baselines.

### 8.2 Visual Regression

- **Tools:** [pytest-mpl](https://github.com/matplotlib/pytest-mpl), `skimage.metrics.structural_similarity`.
- **Workflow:** save segmentation overlays, compare to baselines with tolerances.

### 8.3 Property-Based Testing

- **Library:** [Hypothesis](https://hypothesis.readthedocs.io/).
- **Properties:** non-zero regions, hull volume ≤ bounding-box volume, deterministic compression output.

---

## 9. Performance Benchmarking

### 9.1 Profiling Toolchain

- `cProfile`, [SnakeViz](https://jiffyclub.github.io/snakeviz/) for visualization.
- Target bottlenecks: Felzenszwalb graph build, convex hull computation, FFT loops.

### 9.2 Benchmark Suite

- **Framework:** [pytest-benchmark](https://pytest-benchmark.readthedocs.io/).
- **Metrics:** throughput, latency percentiles, peak RSS, accuracy vs. ground truth.
- **Spec targets:** 5–30 s per 1024×1024 image; <10 ms hull computation with CGAL.

#### Telemetry Fast-Path (INT-014 Track A Phase 4)

| Metric | Result (ms) | Notes |
| ------ | ----------- | ----- |
| Runs | 50 | Stubbed segmenter/analyzer/topology to isolate wiring cost |
| Min | 0.040 | |
| Avg | 0.046 | |
| P95 | 0.070 | Queue idle under synthetic load |
| P99 | 0.119 | Max observed in 50 iterations |

- Queue remained non-blocking with 200 ms emitter delay (see `tests/test_detection_telemetry.py`).
- Measurements taken 2025-11-09 using `tmp/telemetry_latency.py` (PYTHONPATH=src).

---

## 10. Future Research Directions

### 10.1 Vision Foundation Models

- **Paper:** [DINO](https://arxiv.org/abs/2104.14294) — Caron et al. (2021).
- **Idea:** Direct polyform classification for known shapes; retain geometric pipeline for novel detections.

### 10.2 Active Learning

- **Survey:** [Active Learning Algorithms](https://minds.wisconsin.edu/bitstream/handle/1793/60660/TR1648.pdf) — Settles (2009).
- **Library:** [modAL](https://modal-python.readthedocs.io/).
- **Workflow:** low-confidence detections → human annotation → catalog expansion.

### 10.3 Distributed Detection

- **Framework:** [Ray](https://www.ray.io/).
- **Paper:** [Ray: A Distributed Framework for Emerging AI Applications](https://arxiv.org/abs/1712.05889).
- **Use case:** Scale detection across thousands of images with distributed workers.

---

## 11. Documentation & Knowledge Transfer

### 11.1 Operator Runbooks

- **Reference:** [Google SRE book – Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/).
- **Guidance:** capture alert metadata, investigation steps, remediation playbooks, preventative measures.

### 11.2 API Documentation

- **Spec:** [OpenAPI/Swagger](https://swagger.io/specification/).
- **Tooling:** [ReDoc](https://github.com/Redocly/redoc) for polished docs; include fixture-based examples, error catalogs, latency expectations.

---

## 12. Recommended Reading Order

1. **Immediate (Phase 1–2):** Felzenszwalb paper, Quickhull paper, OpenCV memory guide, PyInstaller notes.
2. **Short-term architecture:** Event sourcing, NSGA-II overview, Optuna docs, OpenTelemetry introduction.
3. **Long-term exploration:** DINO ViT paper, Active learning survey, Ray distributed framework.

---

## 13. Integration Checklist

- **Phase 3 – Monitoring Integration:** study event sourcing + SRE troubleshooting, wrap detection telemetry into monitoring loop, plan OpenTelemetry migration.

---

## 14. External Model Notes

- All references verified as of **2025‑11‑08**.
- Architectural diagrams are maintained separately (see integration architecture README).
- This document emphasizes reasoning and decision frameworks; reference code paths are cited inline (e.g., `src/polylog6/detection/segmentation.py`).
- Suggested workflow for research assistants:
  1. Absorb this guide to internalize design goals.
  2. Dive into linked papers/resources for deeper understanding.
  3. Cross-check project files to reconcile theory with current implementation.
  4. Propose improvements or experiments grounded in the referenced literature.

---

**Maintainers:** Track A Detection & Track B Monitoring teams  
**Version:** 1.0 (updated 2025‑11‑08)
