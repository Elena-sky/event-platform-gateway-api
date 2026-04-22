"""Application settings from environment / ``.env`` only (no in-code defaults)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Every field must be set via environment or ``.env``."""

    app_name: str
    app_version: str
    app_env: str
    app_port: int
    log_level: str
    uvicorn_host: str

    rabbitmq_host: str
    rabbitmq_port: int
    rabbitmq_user: str
    rabbitmq_password: str

    rabbitmq_exchange: str
    rabbitmq_exchange_type: str
    rabbitmq_bootstrap_queue: str
    rabbitmq_bootstrap_binding_key: str

    # Management HTTP API (for observability endpoints)
    rabbitmq_http_api_url: str
    rabbitmq_http_api_user: str
    rabbitmq_http_api_password: str
    # Comma-separated queue names to monitor, e.g. "events.created,events.dlq"
    rabbitmq_monitored_queues: str

    # Publisher reliability
    rabbitmq_publish_timeout_seconds: int
    rabbitmq_mandatory_publish: bool

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def rabbitmq_url(self) -> str:
        """AMQP connection URL built from host, port, user, and password."""
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}/"
        )

    @property
    def monitored_queues(self) -> list[str]:
        """Parsed list of queue names from the comma-separated env variable."""
        parts = self.rabbitmq_monitored_queues.split(",")
        return [q.strip() for q in parts if q.strip()]


settings = Settings()
