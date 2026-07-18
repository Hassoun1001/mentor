# Single-service image: builds the frontend, then serves it from the FastAPI
# backend (same origin, so no CORS needed). Run migrations on start.

# ---- stage 1: build the frontend ----
FROM node:20-alpine AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- stage 2: python runtime ----
FROM python:3.13-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MENTOR_ENV=production \
    MENTOR_FRONTEND_DIST_DIR=/app/frontend/dist
WORKDIR /app

# libgomp1 is required at runtime by scikit-learn / scipy. curl is the
# FRED adapter's fallback transport (its WAF rejects Python HTTP stacks
# from datacenter IPs but trusts curl's fingerprint).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

# Install the backend (includes src, models, alembic via the copied tree).
COPY backend/ ./backend/
RUN pip install ./backend

# Stash the baked baseline models so the entrypoint can seed a fresh
# persistent model-store volume on first boot (the volume mount hides the
# baked-in models/ directory). After the first retrain the volume owns the
# champion; the seed is only used when the volume is empty.
RUN cp -r /app/backend/models /app/seed-models 2>/dev/null || mkdir -p /app/seed-models

# Built frontend from stage 1.
COPY --from=frontend /fe/dist ./frontend/dist

COPY backend/scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /app/backend
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
