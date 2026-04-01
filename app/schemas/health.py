"""Response model for the liveness endpoint."""

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """JSON shape of ``GET /health``."""

    model_config = ConfigDict(
        json_schema_extra={"example": {"status": "ok"}},
    )

    status: str = Field(
        ...,
        examples=["ok"],
        description='Always "ok" when this handler runs.',
    )
