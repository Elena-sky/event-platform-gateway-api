"""Load generator for throughput / prefetch tuning experiments.

Sends TOTAL events concurrently (CONCURRENCY workers) to the gateway-api.
Use this to fill the queue, then observe in Prometheus or the management UI:

    rabbitmq_queue_messages_ready{queue="notification.email"}
    rabbitmq_queue_messages_unacknowledged{queue="notification.email"}
    rabbitmq_queue_consumers{queue="notification.email"}

Usage
-----
    # Default: 200 events, 20 concurrent workers
    python scripts/load_generate.py

    # Custom
    python scripts/load_generate.py --total 500 --concurrency 50 --url http://localhost:8000

Mini-challenge B: run with 1 replica then 3 replicas and compare drain time.
Mini-challenge A: change RABBITMQ_PREFETCH=1 / 20 / 100 between runs.
"""

import argparse
import asyncio
import time
import uuid

import httpx

DEFAULT_URL = "http://localhost:8000/events"
DEFAULT_TOTAL = 200
DEFAULT_CONCURRENCY = 20

_sent = 0
_errors = 0


async def _send_event(client: httpx.AsyncClient, url: str, i: int) -> None:
    global _sent, _errors  # noqa: PLW0603
    body = {
        "event_type": "user.registered",
        "source": "load-test",
        "payload": {
            "user_id": i,
            "email": f"user{i}@example.com",
            "request_id": str(uuid.uuid4()),
        },
    }
    try:
        response = await client.post(url, json=body)
        response.raise_for_status()
        _sent += 1
    except Exception as exc:  # noqa: BLE001
        _errors += 1
        print(f"  [error] #{i}: {exc}")


async def _worker(client: httpx.AsyncClient, url: str, indices: range) -> None:
    for i in indices:
        await _send_event(client, url, i)


async def run(url: str, total: int, concurrency: int) -> None:
    print(f"Sending {total} events to {url}  (concurrency={concurrency})")
    batch = total // concurrency
    remainder = total % concurrency

    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = []
        start = 0
        for w in range(concurrency):
            end = start + batch + (1 if w < remainder else 0)
            if start < end:
                tasks.append(_worker(client, url, range(start, end)))
            start = end

        t0 = time.perf_counter()
        await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - t0

    rps = _sent / elapsed if elapsed > 0 else 0
    print(
        f"\nDone in {elapsed:.2f}s — sent={_sent}  errors={_errors}  ({rps:.0f} req/s)"
    )


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Event platform load generator")
    p.add_argument("--url", default=DEFAULT_URL, help="Gateway API URL")
    p.add_argument(
        "--total", type=int, default=DEFAULT_TOTAL, help="Total events to send"
    )
    p.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help="Concurrent workers",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    asyncio.run(run(args.url, args.total, args.concurrency))
