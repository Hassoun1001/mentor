"""Auth endpoints — login + status."""

from __future__ import annotations

import time
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from mentor.api.deps import SettingsDep
from mentor.application.auth import AuthError, AuthService, Credentials

router = APIRouter(prefix="/auth", tags=["auth"])

# Simple in-memory login throttle — enough to blunt brute-force on a
# single-instance personal deploy (per client IP; resets on restart).
_LOGIN_MAX_ATTEMPTS = 10
_LOGIN_WINDOW_SECONDS = 300.0
_login_attempts: dict[str, list[float]] = {}


def _check_login_rate(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    recent = [t for t in _login_attempts.get(ip, []) if now - t < _LOGIN_WINDOW_SECONDS]
    if len(recent) >= _LOGIN_MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="too many login attempts; try again shortly")
    recent.append(now)
    _login_attempts[ip] = recent


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime


class StatusResponse(BaseModel):
    auth_enabled: bool


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, settings: SettingsDep, request: Request) -> LoginResponse:
    _check_login_rate(request)
    service = AuthService(settings)
    try:
        token = service.login(Credentials(username=body.username, password=body.password))
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return LoginResponse(
        access_token=token.access_token,
        token_type=token.token_type,
        expires_at=token.expires_at,
    )


@router.get("/status", response_model=StatusResponse)
async def status(settings: SettingsDep) -> StatusResponse:
    return StatusResponse(auth_enabled=bool(settings.auth_password_hash))
