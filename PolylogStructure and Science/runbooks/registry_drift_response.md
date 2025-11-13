# Registry Drift Detection & Response Runbook

**Last updated:** 2025-11-09  
**Owner:** Storage/Ops Team  
**Applies to:** Monitoring Loop (INT-003/INT-004)

---

## 1. Trigger

A digest mismatch between the stored polyform registry and the live registry captured in `memory/coordination/context-brief.jsonl`.

Detected automatically by `LibraryRefreshWorker` within the monitoring loop.

---

## 2. Alert Signals

| Channel   | Description                                                    |
|-----------|----------------------------------------------------------------|
| Webhook   | JSON payload POSTed to the monitoring endpoint with drift data |
| Email     | Summary alert to [ops@polylog.example](mailto:ops@polylog.example) |
| Dashboard | Banner & remediation link in the monitoring console            |

Alerts are emitted via the fan-out callbacks wired in `polylog6.monitoring.alerts.fanout_alert_callbacks`.

---

## 3. Automated Detection Flow

1. `ContextBriefTailer` polls or watches `context-brief.jsonl` (default: every 5s).
2. Each new checkpoint record provides `registry_digest` metadata.
3. `LibraryRefreshWorker` recomputes the live registry digest.
4. If digests differ:
   - `on_refresh` callback is invoked (auto-refresh attempt).
   - `on_alert` fan-out emits webhook/email/dashboard notifications.
   - Event is logged for audit.

Telemetry snapshots are captured via `DetectionTelemetryBridge` for latency tracing.

---

## 4. Manual Response Procedure

Follow if the automated refresh fails or further investigation is required.

1. **Inspect alert detail**
   - Navigate to the monitoring dashboard alert entry.
   - Review missing/unexpected symbol lists (metadata).

2. **Validate catalog state**

   ```powershell
   $env:PYTHONPATH = 'src'
   .\.venv312\Scripts\python.exe scripts\validate_polyform_schema.py
   ```

3. **Rehydrate catalogs**

   ```powershell
   $env:PYTHONPATH = 'src'
   .\.venv312\Scripts\python.exe scripts\populate_catalogs.py --workers auto
   ```

   - Confirm `catalogs/metadata.json` checksum matches `stable_polyforms.jsonl`.

4. **Recompute digest**
   - Re-run the monitoring loop or invoke `LibraryRefreshWorker.process_record` on the latest checkpoint.
   - Ensure `registry_match` returns `True`.

5. **Verify replicas**
   - Check digest parity across all storage replicas (`registry_state_provider`).

---

## 5. Prevention & Hardening

- Enable feature flag `refresh.enabled=true` in monitoring config to allow automatic refresh.
- Schedule nightly catalog hydration and checksum validation.
- Alert if the stored digest timestamp is older than 1 hour (stale data indicator).
- Maintain regression coverage (`tests/test_monitoring_refresh_e2e.py`) to keep fan-out working.

---

## 6. Escalation Plan

Escalate to the incident channel if:

- Drift persists after manual rehydration.
- Multiple consecutive checkpoints trigger `registry_mismatch` alerts.
- Auto-refresh fails with `registry_provider_error` codes.

When escalating, attach:

- `memory/coordination/context-brief.jsonl` excerpt (last 20 entries).
- Recent `catalogs/metadata.json`.
- Output of schema validation command.

---

## 7. Related Assets

- **E2E regression:** `tests/test_monitoring_refresh_e2e.py`
- **Monitoring alerts helpers:** `src/polylog6/monitoring/alerts.py`
- **Library refresh worker:** `src/polylog6/monitoring/library_refresh.py`
- **Catalog hydration CLI:** `scripts/populate_catalogs.py`
- **Stable polyform dataset:** `./stable_polyforms.jsonl`

---

## 8. Change Log

| Date       | Author   | Notes                              |
|------------|----------|------------------------------------|
| 2025-11-09 | Ops team | Initial runbook covering INT-004. |
