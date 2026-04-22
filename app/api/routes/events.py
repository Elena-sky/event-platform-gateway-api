"""HTTP routes for ingesting domain events."""

from fastapi import APIRouter, HTTPException, status

from app.domain.exceptions import MessageReturnedError, PublishNotConfirmedError
from app.schemas.events import EventIn, PublishResult
from app.services.event_publisher import event_publisher_service

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=PublishResult, status_code=status.HTTP_202_ACCEPTED)
async def publish_event(payload: EventIn) -> PublishResult:
    """Publish an event and wait for broker confirmation.

    Returns 202 only after the broker has confirmed the message.

    Raises:
        422: message was returned by the broker (unroutable — check exchange bindings).
        503: broker did not confirm within the configured timeout.
    """
    try:
        return await event_publisher_service.publish(payload)
    except MessageReturnedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except PublishNotConfirmedError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
