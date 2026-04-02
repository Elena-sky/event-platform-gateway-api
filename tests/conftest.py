"""Shared fixtures: ASGI client with RabbitMQ I/O mocked."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock

from dotenv import load_dotenv

# Required before ``app`` import: ``Settings`` has no code defaults.
load_dotenv(Path(__file__).resolve().parent / "test.env", override=True)

import pytest  # noqa: E402
from app.main import app  # noqa: E402
from app.messaging.rabbitmq import RabbitMQClient, rabbitmq_client  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def mock_broker(monkeypatch: pytest.MonkeyPatch) -> RabbitMQClient:
    """Mock AMQP I/O; keep the singleton so routes publish to ``AsyncMock``."""
    monkeypatch.setattr(rabbitmq_client, "connect", AsyncMock())
    monkeypatch.setattr(rabbitmq_client, "close", AsyncMock())
    monkeypatch.setattr(rabbitmq_client, "publish_event", AsyncMock())
    return rabbitmq_client


@pytest.fixture
def client(mock_broker: RabbitMQClient) -> Generator[TestClient, None, None]:  # noqa: ARG001
    """HTTP client against the app with lifespan (startup/shutdown) executed."""
    with TestClient(app) as test_client:
        yield test_client
