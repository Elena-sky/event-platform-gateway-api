"""RabbitMQ client: topic exchange, bootstrap queue/bindings, persistent publishes."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import aio_pika
from aio_pika import (
    DeliveryMode,
    ExchangeType,
    Message,
    RobustChannel,
    RobustConnection,
)
from aio_pika.abc import AbstractRobustExchange

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _exchange_type_from_settings(name: str) -> ExchangeType:
    key = name.lower().strip()
    mapping: dict[str, ExchangeType] = {
        "topic": ExchangeType.TOPIC,
        "direct": ExchangeType.DIRECT,
        "fanout": ExchangeType.FANOUT,
        "headers": ExchangeType.HEADERS,
    }
    if key not in mapping:
        raise ValueError(
            f"Unsupported RABBITMQ_EXCHANGE_TYPE={name!r}; "
            f"expected one of: {', '.join(sorted(mapping))}"
        )
    return mapping[key]


def _amqp_timestamp(value: Any) -> datetime | None:
    """Coerce payload time for aio_pika (needs ``datetime``, not JSON ISO strings)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return None


class RabbitMQClient:
    def __init__(self) -> None:
        self._connection: RobustConnection | None = None
        self._channel: RobustChannel | None = None
        self._exchange: AbstractRobustExchange | None = None

    async def connect(self) -> None:
        if self._connection and not self._connection.is_closed:
            return

        logger.info(
            "Connecting to RabbitMQ",
            extra={
                "rabbitmq_host": settings.rabbitmq_host,
                "rabbitmq_port": settings.rabbitmq_port,
            },
        )

        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self._channel = await self._connection.channel()

        self._exchange = await self._channel.declare_exchange(
            name=settings.rabbitmq_exchange,
            type=_exchange_type_from_settings(settings.rabbitmq_exchange_type),
            durable=True,
        )

        # Временный bootstrap queue для Дня 3:
        queue = await self._channel.declare_queue(
            name=settings.rabbitmq_bootstrap_queue,
            durable=True,
        )

        await queue.bind(
            exchange=self._exchange,
            routing_key=settings.rabbitmq_bootstrap_binding_key,
        )

        logger.info(
            "RabbitMQ topology initialized",
            extra={
                "exchange": settings.rabbitmq_exchange,
                "exchange_type": settings.rabbitmq_exchange_type,
                "bootstrap_queue": settings.rabbitmq_bootstrap_queue,
                "bootstrap_binding_key": settings.rabbitmq_bootstrap_binding_key,
            },
        )

    async def close(self) -> None:
        """Close channel and connection if they are open."""
        if self._channel and not self._channel.is_closed:
            await self._channel.close()

        if self._connection and not self._connection.is_closed:
            await self._connection.close()

        logger.info("RabbitMQ connection closed")

    async def publish_event(self, routing_key: str, payload: dict) -> None:
        if not self._exchange:
            raise RuntimeError("RabbitMQ exchange is not initialized")

        body = json.dumps(payload, default=str).encode("utf-8")

        message = Message(
            body=body,
            content_type="application/json",
            delivery_mode=DeliveryMode.PERSISTENT,
            type=payload.get("event_type"),
            message_id=str(payload.get("event_id")),
            timestamp=_amqp_timestamp(payload.get("occurred_at")),
        )

        await self._exchange.publish(
            message=message,
            routing_key=routing_key,
        )

        logger.info(
            "Event published to exchange",
            extra={
                "exchange": settings.rabbitmq_exchange,
                "routing_key": routing_key,
                "payload_size": len(body),
            },
        )


rabbitmq_client = RabbitMQClient()
