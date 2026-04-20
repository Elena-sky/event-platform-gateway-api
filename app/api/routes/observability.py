"""Observability endpoints: broker health checks and queue lag metrics."""

from fastapi import APIRouter, HTTPException

from app.monitoring.rabbitmq_http import RabbitMQHttpClient
from app.schemas.observability import BrokerOverview

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get(
    "/broker",
    response_model=BrokerOverview,
    summary="Broker health and queue lag",
    description=(
        "Returns RabbitMQ health-check results (aliveness + node) "
        "and message-lag stats for all configured monitored queues."
    ),
)
async def broker_overview() -> BrokerOverview:
    """Query the RabbitMQ Management HTTP API and aggregate the results."""
    try:
        client = RabbitMQHttpClient()
        return await client.get_overview()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach RabbitMQ Management API: {exc}",
        ) from exc
