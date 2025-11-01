# STAB-004: Performance Budgets

**Status:** Draft  
**Last Updated:** 2025-10-31  
**Owner:** Performance Engineer (TBD)

This table captures the initial frame-time, memory, and job budgets per platform. Values are derived from early profiling on the target hardware set and will serve as guardrails for CI gating.

| Platform | Frame Time Target (ms) | Max Spike (ms) | VRAM Budget (GB) | DRAM Budget (GB) | Draw Calls / Frame | Dispatch Calls / Frame | CPU Job Count / Frame |
|----------|------------------------|----------------|------------------|------------------|--------------------|------------------------|-----------------------|
| Windows (DX12, RTX 3070) | 16.67 | 33.3 | 6.0 | 10.0 | 4,000 | 500 | 300 |
| Linux (Vulkan, RX 6800) | 16.67 | 33.3 | 6.0 | 10.0 | 3,800 | 450 | 280 |
| macOS (Metal, M2 Pro) | 16.67 | 33.3 | 5.0 | 8.0 | 3,000 | 400 | 260 |
| Console Tier 1 (TBD) | 16.67 | 25.0 | 5.5 | 9.0 | 3,500 | 420 | 270 |

## CI Integration Placeholders

* Add `perf_budget.yaml` (to be referenced by CI) listing per-platform limits.  
* Grove CI pipeline will include a "Perf Gates" stage that runs deterministic benchmark scenes and compares against the table above.  
* Budgets feed into KPI `frame_stall_spikes` and `perf_regression` and will be refined after STAB-005 and STAB-006 land.
