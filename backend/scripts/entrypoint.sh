#!/bin/sh
# Container entrypoint: apply DB migrations, then serve the app (API + built
# frontend). Hosts like Render/Railway inject $PORT; default to 8000.
set -e

echo "[entrypoint] running database migrations..."
alembic upgrade head

echo "[entrypoint] starting server on port ${PORT:-8000}..."
exec uvicorn mentor.main:app --host 0.0.0.0 --port "${PORT:-8000}"
