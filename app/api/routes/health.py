"""HTTP routes for process liveness (not broker health)."""

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def healthcheck() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "exchange": settings.rabbitmq_exchange,
    }
