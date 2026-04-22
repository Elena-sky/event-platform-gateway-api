"""Tests for ``POST /events`` (broker-confirmed publish, routing key = event type)."""

import uuid

from app.core.config import settings
from app.domain.exceptions import MessageReturnedError, PublishNotConfirmedError
from app.messaging.rabbitmq import RabbitMQClient
from fastapi.testclient import TestClient

_VALID_EVENT_BODY = {
    "event_type": "user.registered",
    "source": "frontend",
    "payload": {"user_id": 1},
}


def test_post_events_accepted(client: TestClient, mock_broker: RabbitMQClient) -> None:
    response = client.post("/events", json=_VALID_EVENT_BODY)
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


def test_post_events_publish_timeout_returns_503(
    client: TestClient, mock_broker: RabbitMQClient
) -> None:
    mock_broker.publish_event.side_effect = PublishNotConfirmedError(
        f"Broker did not confirm publish within "
        f"{settings.rabbitmq_publish_timeout_seconds}s "
        f"(routing_key=user.registered)"
    )
    response = client.post("/events", json=_VALID_EVENT_BODY)
    assert response.status_code == 503
    assert "Broker did not confirm publish" in response.json()["detail"]


def test_post_events_unroutable_returns_422(
    client: TestClient, mock_broker: RabbitMQClient
) -> None:
    mock_broker.publish_event.side_effect = MessageReturnedError(
        "Broker returned unroutable message for routing_key=user.registered"
    )
    response = client.post("/events", json=_VALID_EVENT_BODY)
    assert response.status_code == 422
    assert "unroutable" in response.json()["detail"]


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
