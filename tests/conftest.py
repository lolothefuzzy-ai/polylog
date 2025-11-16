from __future__ import annotations

import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


@pytest.fixture
def record_storage_metrics(request):
    """Attach storage metrics to the pytest item for JSON report collection."""

    def _record(metrics):
        request.node.user_properties.append(("storage_metrics", metrics))

    return _record
