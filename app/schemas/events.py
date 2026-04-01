"""Pydantic models for HTTP ingress, canonical queue messages, and API responses."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventIn(BaseModel):
    """``POST /events`` body before enrichment (no ``event_id`` / ``occurred_at``)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_type": "user.registered",
                "source": "frontend",
                "payload": {
                    "user_id": 123,
                    "email": "user@example.com",
                },
            }
        },
    )

    event_type: str = Field(
        ...,
        examples=["user.registered"],
        description='Dot-notation name, e.g. "domain.action".',
    )
    source: str = Field(
        ...,
        examples=["frontend"],
        description="Logical producer of the event.",
    )
    payload: dict[str, Any] = Field(
        ...,
        description="Arbitrary JSON object carried to consumers.",
    )

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, value: str) -> str:
        if not value or "." not in value:
            msg = "event_type must follow dot notation, e.g. user.registered"
            raise ValueError(msg)
        return value


class EventMessage(BaseModel):
    """Self-contained message written to the broker (downstream-friendly)."""

    event_id: UUID
    event_type: str
    source: str
    occurred_at: datetime
    payload: dict[str, Any]

    @classmethod
    def from_input(cls, event_in: EventIn) -> EventMessage:
        """Create a message with a new id and current UTC timestamp."""
        return cls(
            event_id=uuid4(),
            event_type=event_in.event_type,
            source=event_in.source,
            occurred_at=datetime.now(UTC),
            payload=event_in.payload,
        )


class PublishResult(BaseModel):
    """Returned to the client after the message is accepted for publishing."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "queue": "events.raw",
                "status": "accepted",
            }
        },
    )

    event_id: UUID
    queue: str
    status: str = "accepted"
