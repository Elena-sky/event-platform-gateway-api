"""Async HTTP client for the RabbitMQ Management HTTP API.

Used exclusively for observability: health checks and queue lag stats.
AMQP traffic stays in ``app/messaging/rabbitmq.py``.
"""

from urllib.parse import quote

import httpx

from app.core.config import settings
from app.schemas.observability import BrokerCheck, BrokerOverview, QueueStats


class RabbitMQHttpClient:
    """Thin wrapper around the RabbitMQ Management HTTP API.

    All methods create a short-lived ``httpx.AsyncClient`` so the client
    object is safe to instantiate per-request (no shared connection pool state).
    """

    def __init__(self) -> None:
        self._base = settings.rabbitmq_http_api_url.rstrip("/")
        self._auth = (
            settings.rabbitmq_http_api_user,
            settings.rabbitmq_http_api_password,
        )
        self._queues = settings.monitored_queues

    async def get_overview(self) -> BrokerOverview:
        """Fetch broker health checks and stats for all monitored queues."""
        vhost = quote("/", safe="")  # %2F — the default virtual host

        async with httpx.AsyncClient(auth=self._auth, timeout=5.0) as client:
            alive_path = f"{self._base}/api/aliveness-test/{vhost}"
            aliveness_resp = await client.get(alive_path)
            node_resp = await client.get(f"{self._base}/api/healthchecks/node")

            queue_stats: list[QueueStats] = []
            for queue_name in self._queues:
                q_resp = await client.get(
                    f"{self._base}/api/queues/{vhost}/{quote(queue_name, safe='')}"
                )
                if q_resp.status_code == 200:
                    d = q_resp.json()
                    queue_stats.append(
                        QueueStats(
                            name=queue_name,
                            messages=d.get("messages", 0),
                            messages_ready=d.get("messages_ready", 0),
                            messages_unacknowledged=d.get("messages_unacknowledged", 0),
                            consumers=d.get("consumers", 0),
                        )
                    )

        return BrokerOverview(
            checks=BrokerCheck(
                aliveness=aliveness_resp.status_code == 200,
                node_health=node_resp.status_code == 200,
            ),
            queues=queue_stats,
        )
