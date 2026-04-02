"""Tests for the liveness route."""

from app.core.config import settings
from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": settings.app_name,
        "exchange": settings.rabbitmq_exchange,
    }
