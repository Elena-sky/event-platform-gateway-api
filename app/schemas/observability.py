"""Pydantic models for observability responses."""

from pydantic import BaseModel, Field

from app.schemas.observability_texts import OBSERVABILITY as _T

_QS = _T["queue_stats"]
_BC = _T["broker_check"]


class QueueStats(BaseModel):
    """Lag and consumer metrics for a single queue."""

    name: str = Field(..., description=_QS["name"])
    messages: int = Field(..., description=_QS["messages"])
    messages_ready: int = Field(..., description=_QS["messages_ready"])
    messages_unacknowledged: int = Field(
        ...,
        description=_QS["messages_unacknowledged"],
    )
    consumers: int = Field(..., description=_QS["consumers"])


class BrokerCheck(BaseModel):
    """Results of RabbitMQ health-check endpoints."""

    aliveness: bool = Field(..., description=_BC["aliveness"])
    node_health: bool = Field(..., description=_BC["node_health"])


class BrokerOverview(BaseModel):
    """Aggregated broker health and queue lag overview."""

    checks: BrokerCheck
    queues: list[QueueStats]
