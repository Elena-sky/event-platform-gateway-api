"""HTTP routes for ingesting domain events."""

from fastapi import APIRouter, status

from app.schemas.events import EventIn, PublishResult
from app.services.event_publisher import event_publisher_service

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=PublishResult, status_code=status.HTTP_202_ACCEPTED)
async def publish_event(payload: EventIn) -> PublishResult:
    """Delegate to ``EventPublisherService.publish``."""
    return await event_publisher_service.publish(payload)
