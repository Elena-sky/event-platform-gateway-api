# event-platform-gateway-api

FastAPI HTTP gateway: accepts events and publishes them to RabbitMQ.

## Repositories

[GitHub: Elena-sky](https://github.com/Elena-sky)

- [event-platform-gateway-api](https://github.com/Elena-sky/event-platform-gateway-api)
- [event-platform-notification-service](https://github.com/Elena-sky/event-platform-notification-service)
- [event-platform-analytics-audit-service](https://github.com/Elena-sky/event-platform-analytics-audit-service)
- [event-platform-retry-orchestrator-service](https://github.com/Elena-sky/event-platform-retry-orchestrator-service)
- [event-platform-infra](https://github.com/Elena-sky/event-platform-infra)

## OpenAPI

The API exposes an **OpenAPI 3** specification generated from route signatures and Pydantic models.

### Live endpoints (running server)

| Resource | URL (use ``APP_PORT`` from ``.env``, e.g. 8000) |
|----------|----------------------------------------|
| **OpenAPI JSON** | http://127.0.0.1:${APP_PORT}/openapi.json |
| **Swagger UI** | http://127.0.0.1:${APP_PORT}/docs |
| **ReDoc** | http://127.0.0.1:${APP_PORT}/redoc |

### Static files (YAML / JSON)

Committed copies for tooling, CI, and clients without calling the API:

| File | Description |
|------|-------------|
| `openapi/openapi.json` | OpenAPI schema as JSON |
| `openapi/openapi.yaml` | Same schema as YAML |

Regenerate after changing routes or schemas (from the repository root, with the venv activated):

```bash
python scripts/export_openapi.py
```

To disable interactive docs in production, set `docs_url=None`, `redoc_url=None` in `FastAPI(...)` (not applied by default).

## Requirements

- **Python 3.12 or 3.13** (3.13 recommended). On **Python 3.14**, installing `pydantic-core` from `requirements.txt` often fails during build — use 3.12/3.13 or wait for wheels for your Python version.
- A running **RabbitMQ** instance (local or from [event-platform-infra](https://github.com/Elena-sky/event-platform-infra)).

## Development

Lint and format with [Ruff](https://docs.astral.sh/ruff/) (`pyproject.toml`):

```bash
pip install -r requirements-dev.txt
ruff check app scripts tests
ruff format app scripts tests
```

Auto-fix safe issues: `ruff check app scripts tests --fix`.

Tests ([pytest](https://pytest.org/)): RabbitMQ is mocked via `monkeypatch` + `AsyncMock`; no broker required.

```bash
pytest
pytest --cov=app --cov-report=term-missing
```

**CI:** on push/PR to `main` or `master`, [`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs **Ruff** (check + format) and **pytest** with coverage on Python **3.12** and **3.13**.

## Quick start

### 1. Infrastructure (RabbitMQ)

From the `event-platform-infra` directory:

```bash
docker compose up -d
```

Defaults: AMQP `localhost:5672`, user/password `admin` / `admin`, management UI: http://localhost:15672

**Docker:** `cp .env.example .env`, then `docker compose up --build`. Compose sets `RABBITMQ_HOST=rabbitmq` and `UVICORN_HOST=0.0.0.0`. Align `EVENT_PLATFORM_NETWORK_NAME` with [event-platform-infra](https://github.com/Elena-sky/event-platform-infra).

### 2. API configuration

```bash
cd event-platform-gateway-api
cp .env.example .env
```

Edit `.env` as needed. **All configuration is required** in `.env` (or the environment): the application has **no in-code defaults** for these settings. See `.env.example` for the full list.

### 3. Virtual environment and dependencies

```bash
python3.13 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run the server

From the repository root (where the `app/` package lives). Load `.env` into the shell so `UVICORN_HOST` and `APP_PORT` match what Pydantic uses:

```bash
set -a && . ./.env && set +a
uvicorn app.main:app --reload --host "$UVICORN_HOST" --port "$APP_PORT"
```

On startup the app **connects to RabbitMQ** in `lifespan`; if the broker is unreachable, the process will exit with an error.

### 5. Verify

- Health: `http://127.0.0.1:${APP_PORT}/health` (after loading `.env`) — expect `status`, `service`, `exchange`.
- OpenAPI: see [OpenAPI](#openapi) (`/openapi.json`, `/docs`, `/redoc`).
- Publish event: `POST /events` (JSON body per `app/schemas/events.py`), response `202 Accepted`.

Example:

```bash
curl -X POST "http://localhost:${APP_PORT}/events" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "user.registered",
    "source": "frontend",
    "payload": {
      "user_id": 123,
      "email": "user@example.com"
    }
  }'
```
