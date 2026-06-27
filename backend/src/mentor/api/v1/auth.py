"""Auth endpoints — login + status."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from mentor.api.deps import SettingsDep
from mentor.application.auth import AuthError, AuthService, Credentials

router = APIRouter(prefix="/auth", tags=["auth"])


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
async def login(body: LoginRequest, settings: SettingsDep) -> LoginResponse:
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
