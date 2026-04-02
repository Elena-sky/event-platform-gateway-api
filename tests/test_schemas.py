"""Unit tests for Pydantic schemas (no HTTP)."""

import uuid

import pytest
from app.schemas.events import EventIn, EventMessage
from pydantic import ValidationError


@pytest.mark.parametrize(
    "event_type",
    [
        "payment.completed",
        "order.created",
        "a.b",
    ],
)
def test_event_in_accepts_valid_event_type(event_type: str) -> None:
    model = EventIn(event_type=event_type, source="s", payload={})
    assert model.event_type == event_type


@pytest.mark.parametrize(
    "event_type",
    [
        "PaymentCompleted",
        "paymentCompleted",
        "PAYMENT.COMPLETED",
        "payment",
        "payment..done",
        ".payment.done",
        "payment.",
    ],
)
def test_event_in_rejects_invalid_event_type(event_type: str) -> None:
    with pytest.raises(ValidationError):
        EventIn(event_type=event_type, source="s", payload={})


def test_event_message_from_input_sets_id_and_timestamp() -> None:
    incoming = EventIn(
        event_type="user.registered",
        source="frontend",
        payload={"x": 1},
    )
    msg = EventMessage.from_input(incoming)
    assert msg.event_type == "user.registered"
    assert msg.source == "frontend"
    assert msg.payload == {"x": 1}
    assert msg.occurred_at.tzinfo is not None
    assert isinstance(msg.event_id, uuid.UUID)
