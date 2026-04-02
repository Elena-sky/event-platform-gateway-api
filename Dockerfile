FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Published port is ``APP_PORT`` from the runtime environment (see ``.env`` / compose).

CMD ["sh", "-c", "exec uvicorn app.main:app --host \"$UVICORN_HOST\" --port \"$APP_PORT\""]