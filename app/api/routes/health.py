"""HTTP routes for process liveness (not broker health)."""

from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Liveness",
    description="Returns **200** when the process is up. Does not check RabbitMQ.",
)
async def healthcheck() -> HealthResponse:
    """Return a minimal JSON body suitable for load balancers."""
    return HealthResponse(status="ok")
