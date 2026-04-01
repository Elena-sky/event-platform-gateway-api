"""Turn validated HTTP input into a broker message and publish to RabbitMQ."""

from app.core.config import settings
from app.core.logging import get_logger
from app.messaging.rabbitmq import rabbitmq_client
from app.schemas.events import EventIn, EventMessage, PublishResult

logger = get_logger(__name__)


class EventPublisherService:
    """Application layer between the events API and the messaging client."""

    async def publish(self, event_in: EventIn) -> PublishResult:
        """Publish ``event_in`` and return queue metadata.

        Args:
            event_in: Validated request body from the HTTP layer.

        Returns:
            Acknowledgement with ``event_id`` and target queue name.
        """
        event_message = EventMessage.from_input(event_in)

        await rabbitmq_client.publish_json(
            routing_key=settings.rabbitmq_queue,
            payload=event_message.model_dump(mode="json"),
        )

        logger.info(
            "Event accepted for publishing",
            extra={
                "event_id": str(event_message.event_id),
                "event_type": event_message.event_type,
            },
        )

        return PublishResult(
            event_id=event_message.event_id,
            queue=settings.rabbitmq_queue,
        )


event_publisher_service = EventPublisherService()
