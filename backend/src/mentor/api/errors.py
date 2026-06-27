"""Domain → HTTP error translation.

Domain code raises plain `DomainError` subclasses; the API layer maps them to
HTTP responses. This keeps the domain pure and framework-free.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from mentor.domain.errors import DomainError, ValidationError


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValidationError)
    async def _validation(request: Request, exc: ValidationError) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=422,
            content={"error": "validation_error", "message": str(exc), "field": exc.field},
        )

    @app.exception_handler(DomainError)
    async def _domain(request: Request, exc: DomainError) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=400,
            content={"error": "domain_error", "message": str(exc)},
        )
