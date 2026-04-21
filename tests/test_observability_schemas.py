"""Unit tests for observability Pydantic schemas (no HTTP, no I/O)."""

import pytest
from pydantic import ValidationError

from app.schemas.observability import BrokerCheck, BrokerOverview, QueueStats


# ---------------------------------------------------------------------------
# QueueStats
# ---------------------------------------------------------------------------


def test_queue_stats_valid_values() -> None:
    qs = QueueStats(
        name="events.created",
        messages=5,
        messages_ready=3,
        messages_unacknowledged=2,
        consumers=1,
    )
    assert qs.name == "events.created"
    assert qs.messages == 5
    assert qs.messages_ready == 3
    assert qs.messages_unacknowledged == 2
    assert qs.consumers == 1


def test_queue_stats_all_zero() -> None:
    qs = QueueStats(
        name="events.dlq",
        messages=0,
        messages_ready=0,
        messages_unacknowledged=0,
        consumers=0,
    )
    assert qs.messages == 0
    assert qs.consumers == 0


def test_queue_stats_missing_consumers_raises() -> None:
    with pytest.raises(ValidationError):
        QueueStats(  # type: ignore[call-arg]
            name="q",
            messages=1,
            messages_ready=1,
            messages_unacknowledged=0,
        )


def test_queue_stats_missing_name_raises() -> None:
    with pytest.raises(ValidationError):
        QueueStats(  # type: ignore[call-arg]
            messages=0,
            messages_ready=0,
            messages_unacknowledged=0,
            consumers=0,
        )


# ---------------------------------------------------------------------------
# BrokerCheck
# ---------------------------------------------------------------------------


def test_broker_check_both_healthy() -> None:
    bc = BrokerCheck(aliveness=True, node_health=True)
    assert bc.aliveness is True
    assert bc.node_health is True


def test_broker_check_aliveness_down() -> None:
    bc = BrokerCheck(aliveness=False, node_health=True)
    assert bc.aliveness is False
    assert bc.node_health is True


def test_broker_check_both_down() -> None:
    bc = BrokerCheck(aliveness=False, node_health=False)
    assert bc.aliveness is False
    assert bc.node_health is False


def test_broker_check_missing_field_raises() -> None:
    with pytest.raises(ValidationError):
        BrokerCheck(aliveness=True)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# BrokerOverview
# ---------------------------------------------------------------------------


def _make_qs(name: str = "q") -> QueueStats:
    return QueueStats(
        name=name,
        messages=1,
        messages_ready=1,
        messages_unacknowledged=0,
        consumers=1,
    )


def test_broker_overview_with_queues() -> None:
    overview = BrokerOverview(
        checks=BrokerCheck(aliveness=True, node_health=True),
        queues=[_make_qs("events.created"), _make_qs("events.dlq")],
    )
    assert len(overview.queues) == 2
    assert overview.queues[0].name == "events.created"
    assert overview.queues[1].name == "events.dlq"


def test_broker_overview_empty_queues() -> None:
    overview = BrokerOverview(
        checks=BrokerCheck(aliveness=False, node_health=False),
        queues=[],
    )
    assert overview.queues == []
    assert overview.checks.aliveness is False


def test_broker_overview_missing_checks_raises() -> None:
    with pytest.raises(ValidationError):
        BrokerOverview(queues=[])  # type: ignore[call-arg]
