# Pattern & Telemetry Benchmarks

**Last updated:** 2025-11-09  
**Owner:** Detection + Monitoring Teams

---

## Phase 3 — Pattern Thresholds

| Metric                    | Value | Notes                                |
|---------------------------|-------|--------------------------------------|
| Symmetry threshold        | 1.00  | `pattern_thresholds.json`             |
| FFT strength threshold    | 0.00  | `pattern_thresholds.json`             |
| FFT peak median           | 12    | Derived from `tune_pattern_thresholds.py` |

Regression coverage: `tests/test_pattern_analysis_real.py`.

---

## Phase 4 — Hull Metrics & Telemetry

### Hull Calibration

| Backend | Avg Volume | Region Count | Deviation |
|---------|------------|--------------|-----------|
| Trimesh | 12.5       | 5            | 0.00%     |
| NumPy   | 12.5       | 5            | 0.00%     |

Source: `scripts/hull_calibration.py` → `tests/fixtures/hull_metrics.json`.

### Telemetry Latency (Target <100 ms)

| Fixture            | Segmentation | Pattern | Hull  | Optimization | Total |
|--------------------|--------------|---------|-------|--------------|-------|
| simple_triangle    | 249.10 ms    | 100.47 ms | 52.73 ms | 0.55 ms      | 372.79 ms |
| grid_pattern       | 4895.13 ms   | 283.08 ms | 1036.51 ms | 8.06 ms     | 6262.63 ms |
| noisy_polyform     | 4467.86 ms   | 428.73 ms | 3350.41 ms | 25.54 ms    | 8117.09 ms |

_Segmentation dominates current runtimes; optimization/caching steps required to reach <100 ms target._

---

## Phase 4 — Compression Baseline (INT-002)

| Metric             | Target | Current | Source                            |
|--------------------|--------|---------|-----------------------------------|
| Tier 1 Compression | ≥85 %  | 90 %    | `compression_metrics.json` (2025-11-09) |
| Tier 2 Compression | ≥65 %  | 70 %    | `compression_metrics.json` (2025-11-09) |

Workflow: `.github/workflows/storage-regression.yml`.

---

## Notes

- Update telemetry table once latency tests land.
- Archive historic metrics by appending dated sections.
