"""FastAPI router for the INT-014 detection pipeline."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, status
from pydantic import BaseModel, Field

from polylog6.monitoring.telemetry_bridge import DetectionTelemetryBridge

from .service import DetectionTask, ImageDetectionService

router = APIRouter(prefix="/detection", tags=["detection"])

_telemetry_bridge = DetectionTelemetryBridge()
_service = ImageDetectionService(telemetry_emitter=_telemetry_bridge.sink())


class AnalyzeRequest(BaseModel):
    image_path: str
    request_id: Optional[str] = None


class AnalyzeAsyncRequest(AnalyzeRequest):
    callback_url: Optional[str] = Field(default=None, description="Future webhook target")


class TelemetryPayload(BaseModel):
    request_id: Optional[str] = None
    region_count: int
    candidate_count: int
    coverage_percent: float
    schema_version: str
    metadata: dict[str, Any] | None = None


@router.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict[str, Any]:
    """Run the detection pipeline synchronously and return plan details."""

    result = _service.analyze(DetectionTask(image_path=request.image_path, request_id=request.request_id))
    plan = result.get("plan")
    if plan is not None:
        result["plan"] = asdict(plan)
    return result


def _invoke_async(task: DetectionTask) -> dict[str, Any]:
    return _service.analyze(task)


@router.post("/analyze_async", status_code=status.HTTP_202_ACCEPTED)
def analyze_async(request: AnalyzeAsyncRequest, background: BackgroundTasks) -> dict[str, Any]:
    """Schedule asynchronous analysis. Callback support will be wired in later phases."""

    task = DetectionTask(image_path=request.image_path, request_id=request.request_id)
    background.add_task(_invoke_async, task)
    return {"status": "accepted"}


@router.post("/telemetry", status_code=status.HTTP_202_ACCEPTED)
def telemetry(payload: TelemetryPayload) -> dict[str, Any]:
    """Accept telemetry payloads emitted by the detection pipeline."""

    _service.emit_telemetry(payload.dict())
    return {"status": "accepted"}


__all__ = ["router"]
