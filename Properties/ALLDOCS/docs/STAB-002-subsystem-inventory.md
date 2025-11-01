# STAB-002: Subsystem Inventory and Ownership Map

**Status:** Draft  
**Last Updated:** 2025-10-31  
**Owner:** Engine Platform PMO

This document catalogs the critical subsystems that influence Polylog stability. Each entry captures scope, primary code locations, current stewardship, and immediate notes/gaps. Ownership reflects accountable leads for decision-making and triage.

| Subsystem | Scope & Responsibilities | Primary Code / Repo | Primary Owner | Backup Owner | Notes / Gaps |
|-----------|-------------------------|----------------------|---------------|--------------|---------------|
| Core Math & Time | Numeric utilities, epsilon policy, time accumulators, deterministic RNG plumbing | `Properties/Code/core`, `Properties/Code/multilevel_cache.py`, forthcoming numeric policy module | Math/Time Lead (A. Chen) | QA Physics Rep (D. Ortiz) | Coordinate with STAB-014 for centralized epsilon config |
| Transform & Scene Graph | Quaternion/matrix hygiene, parent-child hierarchies, spatial indexing | `Properties/Code/spatial_index.py`, `Properties/Code/interaction_manager.py` | Scene Systems Lead (L. Patel) | Tools Lead (K. Sato) | Requires hygiene utilities (STAB-016) |
| Simulation Engine | Fixed-step loop, deterministic execution, task/job scheduling | `Properties/Code/automated_placement_engine.py`, `Properties/Code/continuous_exploration_engine.py` | Engine Runtime Lead (R. Malik) | Platform Architect (S. Vaziri) | STAB-005/006 deliverables will update responsibilities |
| Rendering Pipeline | Device interface, frame graph, visibility, TAA | `Properties/Code/render/`, `Properties/Code/bvh3d.py`, `Properties/Code/polyform_visualizer.py` | Render Tech Lead (M. Garcia) | Graphics QA Lead (P. Nguyen) | Align with bgfx ADR-002 and STAB-008/019/020 |
| Physics & Stability | Physics backend selection, stability analyzer integration, collision systems | `Properties/Code/physics/`, `Properties/Code/stability_analyzer.py` | Physics Lead (E. Novak) | Math/Time Lead (A. Chen) | Pending STAB-012 spike |
| Asset Pipeline | Import/export, deterministic bake, runtime packs | `Properties/Code/stable_library.py`, `Properties/ALLDOCS/stability_backlog.yaml`, `Properties/Code/tools/` | Content Pipeline Lead (J. Rivera) | Build Systems Lead (H. Singh) | Needs STAB-013/025 ownership handoff |
| Tooling & CLI | Developer tools, sandboxes, automation scripts | `Properties/Code/tools/`, `Properties/ALLDOCS/scripts/` | Tools Lead (K. Sato) | DevOps Lead (F. Morales) | Track fuzzing infra for STAB-028 |
| Observability & Telemetry | Metrics ingestion, dashboards, crash reporting | `Properties/ALLDOCS/metrics/`, telemetry connectors (TBD) | Observability Lead (C. Alvarez) | QA Automation Lead (I. Huang) | Requires STAB-003 schema adoption |
| Build & Release | CI/CD, reproducible builds, acceptance gates | `Properties/Code/build*.ps1`, PyInstaller specs | Build Systems Lead (H. Singh) | Release Manager (V. Flores) | Align with STAB-001 reproducible builds policy |
| Governance & Security | SBOM, versioning, sandbox policies | `Properties/ALLDOCS/docs/adr/`, security tooling | Compliance Owner (B. Wright) | Security Engineer (N. Kaur) | Coordinate with STAB-014/028/057 |

## Next Steps

1. Confirm owner assignments with department leads (due Nov 3).
2. Add repository deep-links (Git URLs) once mirrored to canonical repos.
3. Establish quarterly review cadence and integrate with CMDB tooling.
4. Feed inventory into performance budget table (STAB-004) and KPI schema (STAB-003).
