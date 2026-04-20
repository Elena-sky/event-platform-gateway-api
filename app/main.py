"""ASGI entrypoint: FastAPI app, OpenAPI metadata, and RabbitMQ lifespan."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.events import router as events_router
from app.api.routes.health import router as health_router
from app.api.routes.observability import router as observability_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.messaging.rabbitmq import rabbitmq_client

configure_logging()
logger = get_logger(__name__)

OPENAPI_TAGS_METADATA = [
    {
        "name": "health",
        "description": "Process liveness. Use for load balancers and orchestrators.",
    },
    {
        "name": "events",
        "description": "Ingest HTTP events and forward them to RabbitMQ.",
    },
    {
        "name": "observability",
        "description": "RabbitMQ broker health checks and queue lag metrics.",
    },
]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Connect to RabbitMQ on startup and close the client on shutdown."""
    logger.info("Starting application", extra={"app_name": settings.app_name})
    await rabbitmq_client.connect()
    yield
    await rabbitmq_client.close()
    logger.info("Application stopped", extra={"app_name": settings.app_name})


app = FastAPI(
    title=settings.app_name,
    description=(
        "HTTP gateway for domain events. Accepts JSON payloads, validates them, "
        "and publishes messages to RabbitMQ. "
        "Machine-readable **OpenAPI 3** schema: [`/openapi.json`](/openapi.json)."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS_METADATA,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.include_router(health_router)
app.include_router(events_router)
app.include_router(observability_router)
