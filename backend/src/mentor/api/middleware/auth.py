"""Bearer-token middleware.

We deliberately keep this small: open paths are listed explicitly; every
other path inside the API prefix requires a valid JWT. The whitelist is
short — health checks and the login endpoint — so it's easy to audit at
a glance.
"""

from __future__ import annotations

from typing import Final

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from mentor.application.auth import AuthError, AuthService
from mentor.config import Settings

_OPEN_SUFFIXES: Final[tuple[str, ...]] = (
    "/health",
    "/auth/login",
    "/auth/status",
)


def _is_open(path: str, prefix: str) -> bool:
    """Open paths are: docs/openapi, anything outside the API prefix, and
    a tiny whitelist inside it."""
    if path in ("/docs", "/openapi.json") or path.startswith("/docs"):
        return True
    if not path.startswith(prefix):
        return True  # routes outside the versioned API are not gated here
    suffix = path[len(prefix) :]
    return any(suffix == s or suffix.startswith(s + "/") for s in _OPEN_SUFFIXES)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, *, settings: Settings) -> None:
        super().__init__(app)
        self._service = AuthService(settings)
        self._prefix = settings.api_prefix
        # If auth isn't configured, the middleware becomes a no-op. This
        # keeps `docker compose up` friendly for first-time setup while
        # still enforcing auth when a password hash is present.
        self._enabled = bool(settings.auth_password_hash)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self._enabled or _is_open(request.url.path, self._prefix):
            return await call_next(request)

        header = request.headers.get("authorization", "")
        if not header.lower().startswith("bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "unauthorized", "message": "missing bearer token"},
            )
        token = header.split(" ", 1)[1].strip()
        try:
            claims = self._service.verify(token)
        except AuthError as exc:
            return JSONResponse(
                status_code=401,
                content={"error": "unauthorized", "message": str(exc)},
            )

        request.state.auth_claims = claims
        return await call_next(request)
