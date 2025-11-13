"""Alert threshold coverage for monitoring service."""

from __future__ import annotations

from typing import Dict

import pytest

from polylog6.monitoring.alerts import AlertRecord, ListAlertSink
from polylog6.monitoring.service import MonitoringService


@pytest.fixture()
def alert_sink() -> ListAlertSink:
    return ListAlertSink()


@pytest.fixture()
def monitoring_service(alert_sink: ListAlertSink) -> MonitoringService:
    return MonitoringService(alert_sink=alert_sink)


def _alerts_by_code(sink: ListAlertSink) -> Dict[str, AlertRecord]:
    return {record.metadata.get("code", ""): record for record in sink.alerts()}


def test_latency_threshold_alert(monitoring_service: MonitoringService, alert_sink: ListAlertSink) -> None:
    payload = {
        "request_id": "slow",
        "duration_ms": MonitoringService.LATENCY_ALERT_THRESHOLD_MS + 1.0,
        "region_count": 3,
        "schema_version": "0.1",
    }

    monitoring_service.ingest_telemetry(payload)

    alerts = _alerts_by_code(alert_sink)
    slow_alert = alerts.get("slow_detection")
    assert slow_alert is not None
    assert slow_alert.metadata["duration_ms"] == pytest.approx(payload["duration_ms"])


def test_zero_region_alert(monitoring_service: MonitoringService, alert_sink: ListAlertSink) -> None:
    payload = {
        "request_id": "empty",
        "duration_ms": 10.0,
        "region_count": 0,
        "schema_version": "0.1",
    }

    monitoring_service.ingest_telemetry(payload)

    alerts = _alerts_by_code(alert_sink)
    zero_alert = alerts.get("zero_regions")
    assert zero_alert is not None
    assert zero_alert.metadata.get("request_id") == payload["request_id"]


def test_no_alert_for_nominal_payload(monitoring_service: MonitoringService, alert_sink: ListAlertSink) -> None:
    payload = {
        "request_id": "ok",
        "duration_ms": 100.0,
        "region_count": 5,
        "schema_version": "0.1",
    }

    monitoring_service.ingest_telemetry(payload)

    alerts = alert_sink.alerts()
    assert alerts == []
