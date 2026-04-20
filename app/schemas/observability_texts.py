"""OpenAPI field descriptions for observability schemas."""

OBSERVABILITY: dict[str, dict[str, str]] = {
    "queue_stats": {
        "name": "Queue name.",
        "messages": "Total messages in queue (ready + unacked).",
        "messages_ready": "Messages ready for delivery.",
        "messages_unacknowledged": "Messages delivered but not yet acked.",
        "consumers": "Number of active consumers.",
    },
    "broker_check": {
        "aliveness": "True when /api/aliveness-test/%2F returns 200.",
        "node_health": "True when /api/healthchecks/node returns 200.",
    },
}
