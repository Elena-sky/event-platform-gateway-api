"""HTTP routes for ingesting domain events."""

from fastapi import APIRouter, status

from app.schemas.events import EventIn, PublishResult
from app.services.event_publisher import event_publisher_service

router = APIRouter(prefix="/events", tags=["events"])


@router.post(
    "",
    response_model=PublishResult,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Publish an event",
    description=(
        "Validates the body, assigns an `event_id`, serializes the message, "
        "and publishes it to the configured RabbitMQ queue."
    ),
    responses={
        422: {
            "description": (
                "Request body does not match the schema (e.g. invalid `event_type`)."
            ),
        },
    },
)
async def publish_event(payload: EventIn) -> PublishResult:
    """Delegate to ``EventPublisherService.publish``."""
    return await event_publisher_service.publish(payload)
