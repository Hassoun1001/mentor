#!/bin/sh
# Container entrypoint: seed the model store on first boot, apply DB
# migrations, then serve the app (API + built frontend). Hosts like
# Render/Railway inject $PORT; default to 8000.
set -e

# Seed the persistent model-store volume from the image's baked defaults,
# but only when it's empty (first boot). On later boots the volume already
# holds runtime-trained models + the promoted champion, so we leave it alone
# — otherwise every deploy would reset the champion to the baseline.
MODELS_DIR="/app/backend/models"
mkdir -p "$MODELS_DIR"
if [ -z "$(ls -A "$MODELS_DIR" 2>/dev/null)" ] && [ -d /app/seed-models ]; then
  echo "[entrypoint] seeding model store from baked defaults..."
  cp -a /app/seed-models/. "$MODELS_DIR/" 2>/dev/null || true
fi

echo "[entrypoint] running database migrations..."
alembic upgrade head

echo "[entrypoint] starting server on port ${PORT:-8000}..."
exec uvicorn mentor.main:app --host 0.0.0.0 --port "${PORT:-8000}"
