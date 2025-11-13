# Priority 2 — Monitoring Loop (INT-003 / INT-004)

## TASK-MON-001: Config-Based Path Discovery

- **Files:** `config/monitoring.yaml`, `src/polylog6/monitoring/config.py`
- **Dependencies:** `PyYAML`
- **Config Stub (`config/monitoring.yaml`):**

  ```yaml
  context_brief:
    path: "memory/coordination/context-brief.jsonl"
    fallback_paths:
      - "/var/log/polylog/context-brief.jsonl"
      - "C:/ProgramData/Polylog/context-brief.jsonl"
    create_if_missing: true
    poll_interval_ms: 500
  ```

- **Code Stub (`config.py`):**

  ```python
  import os
  from pathlib import Path

  import yaml


  def get_context_brief_path() -> Path:
      if env_path := os.getenv("POLYLOG_CONTEXT_BRIEF_PATH"):
          return Path(env_path)

      config_file = Path("config/monitoring.yaml")
      if config_file.exists():
          config = yaml.safe_load(config_file.read_text())
          primary = Path(config["context_brief"]["path"])
          if primary.exists():
              return primary

          for fallback in config["context_brief"].get("fallback_paths", []):
              candidate = Path(fallback)
              if candidate.exists():
                  return candidate

      return Path("memory/coordination/context-brief.jsonl")
  ```

- **Validation:** unit test ensures environment variable override, config primary, and fallback paths resolve correctly
- **Resources:** <https://pyyaml.org/wiki/PyYAMLDocumentation>

## TASK-MON-002: Rotation-Aware Tailer

- **File:** `src/polylog6/monitoring/context_brief_tailer.py`
- **Dependencies:** `watchdog`
- **Code Sketch:**

  ```python
  import json
  from pathlib import Path

  from watchdog.events import FileSystemEventHandler
  from watchdog.observers import Observer


  class ContextBriefHandler(FileSystemEventHandler):
      def __init__(self, callback):
          self._callback = callback
          self._last_position = 0

      def on_modified(self, event):
          if event.src_path.endswith("context-brief.jsonl"):
              with open(event.src_path, "r", encoding="utf-8") as handle:
                  handle.seek(self._last_position)
                  for line in handle:
                      try:
                          self._callback(json.loads(line))
                      except json.JSONDecodeError:
                          continue
                  self._last_position = handle.tell()

      def on_moved(self, event):
          if event.dest_path.endswith("context-brief.jsonl"):
              self._last_position = 0


  class ContextBriefTailer:
      def __init__(self, path: Path):
          self._path = path
          self._observer = Observer()
          self._handler = ContextBriefHandler(self._emit)

      def watch(self, callback):
          self._emit = callback
          self._observer.schedule(self._handler, str(self._path.parent), recursive=False)
          self._observer.start()

      def stop(self):
          self._observer.stop()
          self._observer.join()
  ```

- **Validation:** manual test rotating file (`mv` + `touch`) should continue delivering new entries without duplication
- **Resources:** <https://python-watchdog.readthedocs.io/>

## TASK-MON-003: Deterministic Digest Computation

- **Files:** `src/polylog6/monitoring/digest.py`, `tests/test_monitoring_digest.py`
- **Dependencies:** none (stdlib)
- **Code Stub (`digest.py`):**

  ```python
  import hashlib
  import json


  def compute_registry_digest(storage_state: dict) -> str:
      canonical = json.dumps(storage_state, sort_keys=True, separators=(",", ":"))
      return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
  ```

- **Test Stub:**

  ```python
  from polylog6.monitoring.digest import compute_registry_digest


  def test_digest_determinism():
      state = {"registry": {"uuid1": {"O": 1}, "uuid2": {"O": 2}}}
      assert compute_registry_digest(state) == compute_registry_digest(state)


  def test_digest_order_independence():
      state_a = {"registry": {"a": 1, "b": 2}}
      state_b = {"registry": {"b": 2, "a": 1}}
      assert compute_registry_digest(state_a) == compute_registry_digest(state_b)
  ```

- **Validation:** pytest module passes; digest length is 64 hex chars and invariant to key order
- **Resources:** Python `hashlib` documentation
