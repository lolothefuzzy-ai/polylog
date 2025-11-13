from fastapi import FastAPI
from fastapi.testclient import TestClient

from polylog6.detection import router, service
from polylog6.detection.service import DetectionTask

app = FastAPI()
app.include_router(router)


class _StubService(service.ImageDetectionService):
    def __init__(self):  # pragma: no cover - simple stub
        pass

    def analyze(self, task: DetectionTask):  # pragma: no cover - simple stub
        return {"plan": {"candidates": [], "coverage_percent": 0.0}}


client = TestClient(app)


def test_analyze_endpoint_returns_plan(monkeypatch):
    stub = _StubService()
    monkeypatch.setattr(service, "ImageDetectionService", lambda: stub, raising=False)

    response = client.post("/detection/analyze", json={"image_path": "foo.png"})
    assert response.status_code == 200
    data = response.json()
    assert "plan" in data


def test_telemetry_endpoint_accepts_payload():
    payload = {
        "region_count": 1,
        "candidate_count": 2,
        "coverage_percent": 10.0,
        "schema_version": "0.1",
    }
    response = client.post("/detection/telemetry", json=payload)
    assert response.status_code == 202
