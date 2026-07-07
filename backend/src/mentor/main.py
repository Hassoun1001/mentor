"""FastAPI application factory.

The module exposes `app` for ASGI servers and `create_app()` for tests.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from mentor import __version__
from mentor.api.errors import install_error_handlers
from mentor.api.middleware.auth import JWTAuthMiddleware
from mentor.api.v1 import api_v1
from mentor.application.scheduler import LoopScheduler
from mentor.config import Settings, get_settings
from mentor.infrastructure.db import build_engine, build_session_factory
from mentor.logging import configure_logging, get_logger


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    log = get_logger("mentor.lifespan")
    log.info("startup", env=settings.env, version=__version__)

    engine = build_engine(settings)
    app.state.engine = engine
    app.state.session_factory = build_session_factory(engine)

    scheduler = LoopScheduler(settings=settings, session_factory=app.state.session_factory)
    app.state.scheduler = scheduler
    scheduler.start()  # no-op unless MENTOR_LOOP_ENABLED

    try:
        yield
    finally:
        scheduler.shutdown()
        await engine.dispose()
        log.info("shutdown")


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    configure_logging(resolved)

    # Fail fast rather than deploy an insecure public API.
    problems = resolved.insecure_production_reasons()
    if problems:
        raise RuntimeError(
            "Refusing to start in production with insecure configuration:\n- "
            + "\n- ".join(problems)
        )
    for warning in resolved.production_warnings():
        get_logger("mentor.startup").warning("config_warning", detail=warning)

    # Don't expose interactive API docs / schema on a public deploy.
    docs_url = None if resolved.is_production else "/docs"
    openapi_url = None if resolved.is_production else "/openapi.json"

    app = FastAPI(
        title="Mentor API",
        version=__version__,
        lifespan=_lifespan,
        docs_url=docs_url,
        redoc_url=None,
        openapi_url=openapi_url,
    )
    app.state.settings = resolved

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["*"],
    )

    app.add_middleware(JWTAuthMiddleware, settings=resolved)

    install_error_handlers(app)
    app.include_router(api_v1, prefix=resolved.api_prefix)

    # Serve the built frontend from this same app (single-service deploy).
    # Mounted last so the API routes above always take precedence. The static
    # shell is intentionally open — the API behind it is what's gated.
    dist = resolved.resolved_frontend_dist
    if dist is not None:
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="frontend")

    return app


app = create_app()
