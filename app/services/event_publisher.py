"""Turn validated HTTP input into a broker message and publish to RabbitMQ."""

from app.core.config import settings
from app.core.logging import get_logger
from app.messaging.rabbitmq import rabbitmq_client
from app.schemas.events import EventIn, EventMessage, PublishResult

logger = get_logger(__name__)


class EventPublisherService:
    async def publish(self, event_in: EventIn) -> PublishResult:
        event_message = EventMessage.from_input(event_in)

        await rabbitmq_client.publish_event(
            routing_key=event_message.event_type,
            payload=event_message.model_dump(mode="json"),
        )

        logger.info(
            "Event broker-confirmed and accepted",
            extra={
                "event_id": str(event_message.event_id),
                "event_type": event_message.event_type,
            },
        )

        return PublishResult(
            event_id=event_message.event_id,
            exchange=settings.rabbitmq_exchange,
            routing_key=event_message.event_type,
        )


event_publisher_service = EventPublisherService()
