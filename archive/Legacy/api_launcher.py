"""Dedicated API launcher for the Polylog desktop build.

Provides a clean entry point that avoids legacy ALLDOCS dependencies and
ensures debug visibility when stdout/stderr bindings are altered on Windows.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import uvicorn


def _debug_streams(prefix: str = "") -> None:
    """Log the status of stdout/stderr to the original error stream."""
    debug_out = sys.__stderr__
    print(f"{prefix}stdout.closed = {sys.stdout.closed}", file=debug_out)
    print(f"{prefix}stderr.closed = {sys.stderr.closed}", file=debug_out)


def start_api(host: str = "127.0.0.1", port: int = 8000, log_level: Optional[str] = None) -> None:
    """Launch the FastAPI server via uvicorn."""

    debug_out = sys.__stderr__
    print("🔍 DEBUG: entering api_launcher.start_api", file=debug_out)
    _debug_streams("🔍 DEBUG: ")

    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    try:
        from Properties.Code.api.server import app  # defer heavy import
        print("✅ DEBUG: FastAPI app imported", file=debug_out)
    except Exception as exc:  # pragma: no cover - import failure is fatal
        print(f"❌ DEBUG: failed to import API server: {exc}", file=debug_out)
        raise

    uvicorn_kwargs = {
        "host": host,
        "port": port,
        "log_config": None,
    }
    if log_level is not None:
        uvicorn_kwargs["log_level"] = log_level

    print(f"🚀 DEBUG: starting uvicorn on {host}:{port}", file=debug_out)
    uvicorn.run(app, **uvicorn_kwargs)


if __name__ == "__main__":
    start_api()
