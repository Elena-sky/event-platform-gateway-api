"""HTTP ingress and broker envelope models (event_type doubles as AMQP routing key)."""

import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

EVENT_TYPE_PATTERN = re.compile(r"^[a-z]+(\.[a-z]+)+$")


class EventIn(BaseModel):
    event_type: str = Field(..., examples=["user.registered"])
    source: str = Field(..., examples=["frontend"])
    payload: dict[str, Any]

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, value: str) -> str:
        if not EVENT_TYPE_PATTERN.match(value):
            raise ValueError(
                "event_type must be lowercase dot notation, e.g. user.registered"
            )
        return value


class EventMessage(BaseModel):
    event_id: UUID
    event_type: str
    source: str
    occurred_at: datetime
    payload: dict[str, Any]

    @classmethod
    def from_input(cls, event_in: "EventIn") -> "EventMessage":
        return cls(
            event_id=uuid4(),
            event_type=event_in.event_type,
            source=event_in.source,
            occurred_at=datetime.now(UTC),
            payload=event_in.payload,
        )


class PublishResult(BaseModel):
    event_id: UUID
    exchange: str
    routing_key: str
    status: str = "accepted"
