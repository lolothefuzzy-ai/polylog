"""Centralised logging utilities for Polylog.

This module provides a single entrypoint for configuring Python's logging
infrastructure across the application.  It exposes ``setup_logging`` for
initialisation and ``get_logger`` as the preferred way to fetch module-specific
loggers.
"""
from __future__ import annotations

import json
import logging
import logging.config
import logging.handlers
from pathlib import Path
from typing import Any, Dict, Optional

try:  # Optional dependency – only required when YAML configs are used.
    import yaml  # type: ignore
except Exception:  # pragma: no cover - fallback when PyYAML is absent.
    yaml = None


_REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = _REPO_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

_DEFAULT_LOG_FILE = LOG_DIR / "polylog.log"

_DEFAULT_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        },
        "structured": {
            "format": "%(asctime)s %(name)s %(levelname)s %(module)s:%(lineno)d %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "console",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "structured",
            "filename": str(_DEFAULT_LOG_FILE),
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
            "encoding": "utf-8",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
}


def _load_file_config(config_path: Path) -> Dict[str, Any]:
    """Load a logging configuration from JSON or YAML."""

    suffix = config_path.suffix.lower()
    if suffix in {".json", ".js"}:
        return json.loads(config_path.read_text(encoding="utf-8"))
    if suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError(
                "YAML logging config requested but PyYAML is not installed."
            )
        return yaml.safe_load(config_path.read_text(encoding="utf-8"))
    raise ValueError(f"Unsupported logging config format: {config_path}")


def setup_logging(
    config_path: Optional[Path] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> None:
    """Initialise the logging stack.

    Parameters
    ----------
    config_path:
        Optional path to a JSON/YAML file containing a dictConfig payload.
    overrides:
        Optional dictionary merged into the resolved configuration for quick
        runtime tweaks (e.g., raising the root level during tests).
    """

    if config_path is not None:
        config = _load_file_config(config_path)
    else:
        config = dict(_DEFAULT_CONFIG)

    if overrides:
        # Shallow merge is sufficient for current use-cases.
        config.update(overrides)

    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """Return a module-specific logger configured via ``setup_logging``."""

    return logging.getLogger(name)


def ensure_logging_initialised() -> None:
    """Safeguard for modules that require logging but may run standalone."""

    if not logging.getLogger().handlers:
        setup_logging()


__all__ = ["setup_logging", "get_logger", "ensure_logging_initialised", "LOG_DIR"]
