# event-platform-gateway-api

FastAPI HTTP gateway: accepts events and publishes them to RabbitMQ.

## OpenAPI

The API exposes an **OpenAPI 3** specification generated from route signatures and Pydantic models.

### Live endpoints (running server)

| Resource | URL (default dev server on port 8004) |
|----------|----------------------------------------|
| **OpenAPI JSON** | http://127.0.0.1:8004/openapi.json |
| **Swagger UI** | http://127.0.0.1:8004/docs |
| **ReDoc** | http://127.0.0.1:8004/redoc |

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
- A running **RabbitMQ** instance (local or from the `event-platform-infra` repo).

## Development

Lint and format with [Ruff](https://docs.astral.sh/ruff/) (`pyproject.toml`):

```bash
pip install -r requirements-dev.txt
ruff check app scripts
ruff format app scripts
```

Auto-fix safe issues: `ruff check app scripts --fix`.

## Quick start

### 1. Infrastructure (RabbitMQ)

From the `event-platform-infra` directory:

```bash
docker compose up -d
```

Defaults: AMQP `localhost:5672`, user/password `admin` / `admin`, management UI: http://localhost:15672

### 2. API configuration

```bash
cd event-platform-gateway-api
cp .env.example .env
```

Edit `.env` as needed; see `.env.example` for variables.

### 3. Virtual environment and dependencies

```bash
python3.13 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run the server

From the repository root (where the `app/` package lives):

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8004
```

On startup the app **connects to RabbitMQ** in `lifespan`; if the broker is unreachable, the process will exit with an error.

### 5. Verify

- Health: http://127.0.0.1:8004/health → `{"status":"ok"}`
- OpenAPI: see [OpenAPI](#openapi) (`/openapi.json`, `/docs`, `/redoc`).
- Publish event: `POST /events` (JSON body per `app/schemas/events.py`), response `202 Accepted`.

Example:

```bash
curl -X POST http://localhost:8004/events \
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
