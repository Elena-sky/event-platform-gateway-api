"""Integration tests for GET /observability/broker.

RabbitMQHttpClient is replaced with a mock so no real HTTP connections are made.
The ``client`` fixture from conftest.py already mocks AMQP I/O.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from app.schemas.observability import BrokerCheck, BrokerOverview, QueueStats
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------

_HEALTHY_OVERVIEW = BrokerOverview(
    checks=BrokerCheck(aliveness=True, node_health=True),
    queues=[
        QueueStats(
            name="events.created",
            messages=2,
            messages_ready=2,
            messages_unacknowledged=0,
            consumers=1,
        ),
        QueueStats(
            name="events.dlq",
            messages=0,
            messages_ready=0,
            messages_unacknowledged=0,
            consumers=0,
        ),
    ],
)


def _make_mock_client(
    return_value: BrokerOverview | None = None,
    side_effect: Exception | None = None,
) -> MagicMock:
    """Return a fake RabbitMQHttpClient instance."""
    instance = MagicMock()
    if side_effect is not None:
        instance.get_overview = AsyncMock(side_effect=side_effect)
    else:
        overview = return_value if return_value is not None else _HEALTHY_OVERVIEW
        instance.get_overview = AsyncMock(return_value=overview)
    return instance


# ---------------------------------------------------------------------------
# Success cases
# ---------------------------------------------------------------------------


def test_broker_overview_returns_200(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.api.routes.observability.RabbitMQHttpClient",
        lambda: _make_mock_client(),
    )
    response = client.get("/observability/broker")
    assert response.status_code == 200


def test_broker_overview_checks_structure(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.api.routes.observability.RabbitMQHttpClient",
        lambda: _make_mock_client(),
    )
    data = client.get("/observability/broker").json()
    assert data["checks"]["aliveness"] is True
    assert data["checks"]["node_health"] is True


def test_broker_overview_queues_structure(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.api.routes.observability.RabbitMQHttpClient",
        lambda: _make_mock_client(),
    )
    data = client.get("/observability/broker").json()
    assert len(data["queues"]) == 2
    assert data["queues"][0]["name"] == "events.created"
    assert data["queues"][0]["messages"] == 2
    assert data["queues"][1]["name"] == "events.dlq"
    assert data["queues"][1]["consumers"] == 0


def test_broker_overview_empty_queues(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    overview = BrokerOverview(
        checks=BrokerCheck(aliveness=True, node_health=True),
        queues=[],
    )
    monkeypatch.setattr(
        "app.api.routes.observability.RabbitMQHttpClient",
        lambda: _make_mock_client(return_value=overview),
    )
    data = client.get("/observability/broker").json()
    assert data["queues"] == []


def test_broker_overview_degraded_broker(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    overview = BrokerOverview(
        checks=BrokerCheck(aliveness=False, node_health=True),
        queues=[],
    )
    monkeypatch.setattr(
        "app.api.routes.observability.RabbitMQHttpClient",
        lambda: _make_mock_client(return_value=overview),
    )
    data = client.get("/observability/broker").json()
    # 200 with degraded flags — caller interprets checks in the payload
    assert data["checks"]["aliveness"] is False
    assert data["checks"]["node_health"] is True


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_broker_overview_503_on_connection_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.api.routes.observability.RabbitMQHttpClient",
        lambda: _make_mock_client(side_effect=ConnectionError("Connection refused")),
    )
    response = client.get("/observability/broker")
    assert response.status_code == 503
    assert "Could not reach RabbitMQ Management API" in response.json()["detail"]


def test_broker_overview_503_on_timeout(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.api.routes.observability.RabbitMQHttpClient",
        lambda: _make_mock_client(side_effect=httpx.TimeoutException("timed out")),
    )
    response = client.get("/observability/broker")
    assert response.status_code == 503


def test_broker_overview_503_detail_contains_error_message(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.api.routes.observability.RabbitMQHttpClient",
        lambda: _make_mock_client(side_effect=RuntimeError("unexpected failure")),
    )
    response = client.get("/observability/broker")
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert "unexpected failure" in detail
