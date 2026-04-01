"""RabbitMQ client: durable queue, persistent publishes, reused connection/channel."""

from __future__ import annotations

import json
from typing import Any

import aio_pika
from aio_pika import DeliveryMode, Message, RobustChannel, RobustConnection

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RabbitMQClient:
    """Wraps aio-pika robust connection and a single channel for publishing.

    The queue is declared on :meth:`connect` so local dev works without separate
    topology provisioning; production may later move declarations to infra.
    """

    def __init__(self) -> None:
        self._connection: RobustConnection | None = None
        self._channel: RobustChannel | None = None

    async def connect(self) -> None:
        """Open connection and channel, declare the configured queue if needed."""
        if self._connection and not self._connection.is_closed:
            return

        logger.info("Connecting to RabbitMQ", extra={"url": settings.rabbitmq_url})

        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self._channel = await self._connection.channel()

        await self._channel.declare_queue(
            settings.rabbitmq_queue,
            durable=True,
        )

        logger.info(
            "RabbitMQ connected",
            extra={"queue": settings.rabbitmq_queue},
        )

    async def close(self) -> None:
        """Close channel and connection if they are open."""
        if self._channel and not self._channel.is_closed:
            await self._channel.close()

        if self._connection and not self._connection.is_closed:
            await self._connection.close()

        logger.info("RabbitMQ connection closed")

    async def publish_json(self, routing_key: str, payload: dict[str, Any]) -> None:
        """Publish ``payload`` as JSON via default exchange and ``routing_key``."""
        if not self._channel or self._channel.is_closed:
            raise RuntimeError("RabbitMQ channel is not initialized")

        body = json.dumps(payload, default=str).encode("utf-8")

        message = Message(
            body=body,
            content_type="application/json",
            delivery_mode=DeliveryMode.PERSISTENT,
        )

        await self._channel.default_exchange.publish(
            message,
            routing_key=routing_key,
        )

        logger.info(
            "Message published",
            extra={
                "routing_key": routing_key,
                "payload_size": len(body),
            },
        )


rabbitmq_client = RabbitMQClient()
