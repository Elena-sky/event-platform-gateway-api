"""Tests for ``POST /events`` (topic exchange, routing key = event type)."""

import uuid

from app.core.config import settings
from app.messaging.rabbitmq import RabbitMQClient
from fastapi.testclient import TestClient


def test_post_events_accepted(client: TestClient, mock_broker: RabbitMQClient) -> None:
    body = {
        "event_type": "user.registered",
        "source": "frontend",
        "payload": {"user_id": 1},
    }
    response = client.post("/events", json=body)
    assert response.status_code == 202
    data = response.json()
    assert data["exchange"] == settings.rabbitmq_exchange
    assert data["routing_key"] == "user.registered"
    assert data["status"] == "accepted"
    uuid.UUID(data["event_id"])

    mock_broker.publish_event.assert_awaited_once()
    call = mock_broker.publish_event.await_args
    assert call is not None
    routing_key = call.kwargs["routing_key"]
    payload = call.kwargs["payload"]
    assert routing_key == "user.registered"
    assert payload["event_type"] == "user.registered"
    assert payload["source"] == "frontend"
    assert payload["payload"] == {"user_id": 1}
    assert "event_id" in payload
    assert "occurred_at" in payload


def test_post_events_invalid_event_type_camel_case(client: TestClient) -> None:
    body = {
        "event_type": "PaymentCompleted",
        "source": "frontend",
        "payload": {},
    }
    response = client.post("/events", json=body)
    assert response.status_code == 422


def test_post_events_invalid_event_type_no_dot(client: TestClient) -> None:
    body = {
        "event_type": "paymentcompleted",
        "source": "frontend",
        "payload": {},
    }
    response = client.post("/events", json=body)
    assert response.status_code == 422


def test_post_events_invalid_event_type_uppercase_segment(client: TestClient) -> None:
    body = {
        "event_type": "payment.Completed",
        "source": "frontend",
        "payload": {},
    }
    response = client.post("/events", json=body)
    assert response.status_code == 422
