"""Application settings loaded from environment variables and optional ``.env`` file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration.

    Values are read from the process environment and from a ``.env`` file in the working
    directory (see ``model_config``). Uppercase names such as ``RABBITMQ_HOST`` map to
    fields here.
    """

    app_name: str = "event-platform-gateway-api"
    app_version: str = "0.1.0"
    app_env: str = "dev"
    app_port: int = 8000
    log_level: str = "INFO"

    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "admin"
    rabbitmq_password: str = "admin"
    rabbitmq_queue: str = "events.raw"
    rabbitmq_exchange: str = ""

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


settings = Settings()
