"""Configuration helpers for monitoring feature gating (INT-003/INT-004)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

DEFAULT_CONFIG_PATH = Path("config/monitoring.yaml")
DEFAULT_CONTEXT_BRIEF_PATH = Path("memory/coordination/context-brief.jsonl")
DEFAULT_POLL_INTERVAL_SECONDS = 0.5

_TRUE_VALUES = {"1", "true", "on", "yes"}
_FALSE_VALUES = {"0", "false", "off", "no"}

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore


@dataclass(slots=True)
class ContextBriefSettings:
    """File discovery settings for context-brief tailing."""

    path: Path
    fallback_paths: tuple[Path, ...]
    create_if_missing: bool
    poll_interval_seconds: float


@dataclass(slots=True)
class MonitoringSettings:
    """Aggregated monitoring configuration."""

    enabled: bool
    context_brief: ContextBriefSettings


def _coerce_bool(value: Any, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in _TRUE_VALUES:
            return True
        if lowered in _FALSE_VALUES:
            return False
    return default


def _as_path_sequence(values: Sequence[Any] | None) -> tuple[Path, ...]:
    if not values:
        return ()
    return tuple(Path(str(item)) for item in values if item)


def _load_yaml_config(config_path: Path) -> Mapping[str, Any] | None:
    if yaml is None or not config_path.exists():
        return None
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return data if isinstance(data, Mapping) else None


@lru_cache(maxsize=1)
def load_monitoring_settings(config_path: Path = DEFAULT_CONFIG_PATH) -> MonitoringSettings:
    """Load monitoring settings from environment overrides and optional YAML."""

    env_enabled = os.getenv("POLYLOG_MONITORING_ENABLED")
    env_context_path = os.getenv("POLYLOG_CONTEXT_BRIEF_PATH")
    env_poll_ms = os.getenv("POLYLOG_MONITORING_POLL_MS")

    yaml_config = _load_yaml_config(config_path) or {}
    context_cfg = yaml_config.get("context_brief", {}) if isinstance(yaml_config, Mapping) else {}

    path = Path(env_context_path) if env_context_path else Path(
        str(context_cfg.get("path", DEFAULT_CONTEXT_BRIEF_PATH))
    )

    fallback_values = context_cfg.get("fallback_paths") if isinstance(context_cfg, Mapping) else None
    fallback_paths = _as_path_sequence(fallback_values)

    create_if_missing = _coerce_bool(
        context_cfg.get("create_if_missing"),
        default=False,
    )

    poll_interval_seconds = DEFAULT_POLL_INTERVAL_SECONDS
    if env_poll_ms:
        try:
            poll_interval_seconds = max(float(env_poll_ms) / 1000.0, 0.0)
        except ValueError:
            poll_interval_seconds = DEFAULT_POLL_INTERVAL_SECONDS
    elif isinstance(context_cfg, Mapping) and "poll_interval_ms" in context_cfg:
        try:
            poll_interval_seconds = max(float(context_cfg["poll_interval_ms"]) / 1000.0, 0.0)
        except (TypeError, ValueError):
            poll_interval_seconds = DEFAULT_POLL_INTERVAL_SECONDS

    context_settings = ContextBriefSettings(
        path=path,
        fallback_paths=fallback_paths,
        create_if_missing=create_if_missing,
        poll_interval_seconds=poll_interval_seconds,
    )

    enabled_default = yaml_config.get("enabled", True) if isinstance(yaml_config, Mapping) else True
    enabled = _coerce_bool(env_enabled, default=_coerce_bool(enabled_default, default=True))

    return MonitoringSettings(enabled=enabled, context_brief=context_settings)


def monitoring_enabled() -> bool:
    """Return whether the monitoring loop should run (feature flag)."""

    return load_monitoring_settings().enabled


def resolve_context_brief_path(*, ensure_exists: bool = False) -> Path:
    """Resolve the best context-brief path using environment and config fallbacks."""

    settings = load_monitoring_settings().context_brief

    candidate_paths: Iterable[Path] = (settings.path,) + settings.fallback_paths
    for candidate in candidate_paths:
        if candidate.exists():
            return candidate

    target = settings.path
    if ensure_exists and settings.create_if_missing:
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            target.touch(exist_ok=True)
        except OSError:
            # Ignore filesystem errors so callers can decide how to proceed.
            pass
    return target


def monitoring_poll_interval() -> float:
    """Preferred poll interval (seconds) for the monitoring loop."""

    return load_monitoring_settings().context_brief.poll_interval_seconds
