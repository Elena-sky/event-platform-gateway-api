"""Unit tests for RabbitMQHttpClient (httpx I/O fully mocked).

``test.env`` defines two monitored queues: events.created, events.dlq.
Each ``get_overview()`` call therefore issues exactly 4 GET requests:
  1. /api/aliveness-test/%2F
  2. /api/healthchecks/node
  3. /api/queues/%2F/events.created
  4. /api/queues/%2F/events.dlq
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from app.monitoring.rabbitmq_http import RabbitMQHttpClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_QUEUE_PAYLOAD = {
    "messages": 10,
    "messages_ready": 8,
    "messages_unacknowledged": 2,
    "consumers": 1,
}


def _run(coro: Coroutine[Any, Any, Any]) -> Any:
    return asyncio.run(coro)


def _make_resp(status: int, data: dict[str, Any] | None = None) -> MagicMock:
    """Minimal httpx.Response lookalike."""
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = data or {}
    return resp


def _patch_httpx(responses: list[MagicMock]):  # noqa: ANN201
    """Context manager that replaces ``httpx.AsyncClient`` with a mock
    whose ``.get()`` returns *responses* in order."""
    mock_session = AsyncMock()
    mock_session.get = AsyncMock(side_effect=responses)

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    return patch("app.monitoring.rabbitmq_http.httpx.AsyncClient", return_value=mock_cm)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_all_healthy_full_overview() -> None:
    responses = [
        _make_resp(200),  # aliveness ok
        _make_resp(200),  # node health ok
        _make_resp(200, _QUEUE_PAYLOAD),  # events.created
        _make_resp(200, _QUEUE_PAYLOAD),  # events.dlq
    ]
    with _patch_httpx(responses):
        result = _run(RabbitMQHttpClient().get_overview())

    assert result.checks.aliveness is True
    assert result.checks.node_health is True
    assert len(result.queues) == 2
    assert result.queues[0].name == "events.created"
    assert result.queues[1].name == "events.dlq"


def test_queue_fields_mapped_correctly() -> None:
    payload = {
        "messages": 100,
        "messages_ready": 70,
        "messages_unacknowledged": 30,
        "consumers": 3,
    }
    responses = [
        _make_resp(200),
        _make_resp(200),
        _make_resp(200, payload),  # events.created
        _make_resp(404),  # events.dlq not found
    ]
    with _patch_httpx(responses):
        result = _run(RabbitMQHttpClient().get_overview())

    q = result.queues[0]
    assert q.name == "events.created"
    assert q.messages == 100
    assert q.messages_ready == 70
    assert q.messages_unacknowledged == 30
    assert q.consumers == 3


# ---------------------------------------------------------------------------
# Health check failures
# ---------------------------------------------------------------------------


def test_aliveness_failure_reflected_in_checks() -> None:
    responses = [
        _make_resp(503),  # aliveness fails
        _make_resp(200),  # node health ok
        _make_resp(200, _QUEUE_PAYLOAD),
        _make_resp(200, _QUEUE_PAYLOAD),
    ]
    with _patch_httpx(responses):
        result = _run(RabbitMQHttpClient().get_overview())

    assert result.checks.aliveness is False
    assert result.checks.node_health is True


def test_node_health_failure_reflected_in_checks() -> None:
    responses = [
        _make_resp(200),  # aliveness ok
        _make_resp(503),  # node health fails
        _make_resp(200, _QUEUE_PAYLOAD),
        _make_resp(200, _QUEUE_PAYLOAD),
    ]
    with _patch_httpx(responses):
        result = _run(RabbitMQHttpClient().get_overview())

    assert result.checks.aliveness is True
    assert result.checks.node_health is False


def test_both_health_checks_failing() -> None:
    responses = [
        _make_resp(503),
        _make_resp(503),
        _make_resp(200, _QUEUE_PAYLOAD),
        _make_resp(200, _QUEUE_PAYLOAD),
    ]
    with _patch_httpx(responses):
        result = _run(RabbitMQHttpClient().get_overview())

    assert result.checks.aliveness is False
    assert result.checks.node_health is False


# ---------------------------------------------------------------------------
# Queue availability
# ---------------------------------------------------------------------------


def test_queue_not_found_omitted_from_results() -> None:
    responses = [
        _make_resp(200),
        _make_resp(200),
        _make_resp(200, _QUEUE_PAYLOAD),  # events.created found
        _make_resp(404),  # events.dlq missing
    ]
    with _patch_httpx(responses):
        result = _run(RabbitMQHttpClient().get_overview())

    assert len(result.queues) == 1
    assert result.queues[0].name == "events.created"


def test_all_queues_missing_returns_empty_list() -> None:
    responses = [
        _make_resp(200),
        _make_resp(200),
        _make_resp(404),  # events.created missing
        _make_resp(404),  # events.dlq missing
    ]
    with _patch_httpx(responses):
        result = _run(RabbitMQHttpClient().get_overview())

    assert result.queues == []


def test_missing_queue_fields_default_to_zero() -> None:
    """Management API may omit count fields on a freshly-declared queue."""
    responses = [
        _make_resp(200),
        _make_resp(200),
        _make_resp(200, {}),  # empty payload — all counts absent
        _make_resp(404),
    ]
    with _patch_httpx(responses):
        result = _run(RabbitMQHttpClient().get_overview())

    q = result.queues[0]
    assert q.messages == 0
    assert q.messages_ready == 0
    assert q.messages_unacknowledged == 0
    assert q.consumers == 0
