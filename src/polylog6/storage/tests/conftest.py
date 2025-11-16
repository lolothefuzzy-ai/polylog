from __future__ import annotations

import pytest


@pytest.fixture
def record_storage_metrics(request):
    """Attach storage metrics to the pytest item for JSON report collection."""

    def _record(metrics):
        request.node.user_properties.append(("storage_metrics", metrics))

    return _record
