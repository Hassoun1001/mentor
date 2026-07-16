"""Auth endpoints — login, self-service password change, user management.

Multi-user with per-tab privileges. The first successful login against
the env-configured credentials seeds the `users` table with that account
as the admin; from then on every login is a database lookup. Admins can
create additional accounts and choose exactly which UI tabs each one may
see; those tab ids ride inside the JWT so the frontend can trim its
navigation without an extra round-trip.

Honest scope note: tab privileges gate the *UI*. Every authenticated
user holds a valid API token; this is visibility control for trusted
people (family, a friend you share tips with), not a hard multi-tenant
security boundary.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Final

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from mentor.api.deps import SessionDep, SettingsDep
from mentor.application.auth import (
    AuthService,
    TokenClaims,
    hash_password,
    verify_password,
)
from mentor.infrastructure.models import UserORM
from mentor.infrastructure.repositories.users import (
    UserRepository,
    tabs_from_json,
    tabs_to_json,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Canonical UI tab ids an account can be granted. Kept in sync with the
# frontend's Page union; "settings" is intentionally absent — everyone may
# change their own password.
ALL_TABS: Final[tuple[str, ...]] = (
    "dashboard",
    "forecast",
    "system",
    "loop",
    "trade",
    "tips",
    "risk",
    "journal",
    "lessons",
    "prices",
    "data",
    "backtest",
)

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


def _claims(request: Request) -> TokenClaims | None:
    return getattr(request.state, "auth_claims", None)


def _require_admin(request: Request) -> TokenClaims:
    claims = _claims(request)
    # When auth is disabled (no password hash configured — local dev), the
    # middleware never sets claims; treat the caller as the implicit admin.
    if claims is None:
        now = datetime.now(UTC)
        return TokenClaims(
            subject="mentor", issued_at=now, expires_at=now, is_admin=True, tabs=None
        )
    if not claims.is_admin:
        raise HTTPException(status_code=403, detail="admin privileges required")
    return claims


def _validate_tabs(tabs: list[str] | None) -> tuple[str, ...] | None:
    if tabs is None:
        return None
    unknown = sorted(set(tabs) - set(ALL_TABS))
    if unknown:
        raise HTTPException(status_code=400, detail=f"unknown tabs: {', '.join(unknown)}")
    return tuple(sorted(set(tabs)))


async def _seed_admin_if_empty(repo: UserRepository, settings: SettingsDep) -> None:
    """First boot: promote the env-configured credentials into the users table."""
    if settings.auth_password_hash and await repo.count() == 0:
        await repo.create(
            username=settings.auth_username,
            password_hash=settings.auth_password_hash,
            is_admin=True,
            allowed_tabs=None,
        )


def _user_tabs(user: UserORM) -> tuple[str, ...] | None:
    tabs = tabs_from_json(user.allowed_tabs)
    return None if tabs is None else tuple(tabs)


# ---------- login / status / me ----------


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime
    username: str
    is_admin: bool
    tabs: list[str] | None  # null = every tab


class StatusResponse(BaseModel):
    auth_enabled: bool


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest, settings: SettingsDep, session: SessionDep, request: Request
) -> LoginResponse:
    _check_login_rate(request)
    if not settings.auth_password_hash:
        raise HTTPException(status_code=401, detail="auth not configured on this server")

    repo = UserRepository(session)
    await _seed_admin_if_empty(repo, settings)
    user = await repo.get_by_username(body.username.strip())
    # Verify against a dummy hash on unknown users so response timing
    # doesn't reveal which usernames exist.
    target_hash = user.password_hash if user else settings.auth_password_hash
    password_ok = verify_password(body.password, target_hash)
    if user is None or not password_ok:
        raise HTTPException(status_code=401, detail="invalid credentials")
    await session.commit()  # persist the seed row if this was first login

    tabs = _user_tabs(user)
    token = AuthService(settings).issue_token(user.username, is_admin=user.is_admin, tabs=tabs)
    return LoginResponse(
        access_token=token.access_token,
        token_type=token.token_type,
        expires_at=token.expires_at,
        username=user.username,
        is_admin=user.is_admin,
        tabs=None if tabs is None else list(tabs),
    )


@router.get("/status", response_model=StatusResponse)
async def status(settings: SettingsDep) -> StatusResponse:
    return StatusResponse(auth_enabled=bool(settings.auth_password_hash))


class MeResponse(BaseModel):
    username: str
    is_admin: bool
    tabs: list[str] | None  # null = every tab
    all_tabs: list[str]


@router.get("/me", response_model=MeResponse)
async def me(request: Request, settings: SettingsDep) -> MeResponse:
    claims = _claims(request)
    if claims is None:  # auth disabled (dev) — implicit admin
        return MeResponse(
            username=settings.auth_username, is_admin=True, tabs=None, all_tabs=list(ALL_TABS)
        )
    return MeResponse(
        username=claims.subject,
        is_admin=claims.is_admin,
        tabs=None if claims.tabs is None else list(claims.tabs),
        all_tabs=list(ALL_TABS),
    )


# ---------- self-service password change ----------


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class OkResponse(BaseModel):
    ok: bool = True
    message: str = ""


@router.post("/change-password", response_model=OkResponse)
async def change_password(
    body: ChangePasswordRequest, request: Request, settings: SettingsDep, session: SessionDep
) -> OkResponse:
    claims = _claims(request)
    if claims is None:
        raise HTTPException(status_code=400, detail="auth is disabled on this server")
    repo = UserRepository(session)
    await _seed_admin_if_empty(repo, settings)
    user = await repo.get_by_username(claims.subject)
    if user is None:
        raise HTTPException(status_code=404, detail="account no longer exists")
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=401, detail="current password is incorrect")
    user.password_hash = hash_password(body.new_password)
    await session.commit()
    return OkResponse(message="password updated — it takes effect on your next login")


# ---------- admin: user management ----------


class UserDTO(BaseModel):
    username: str
    is_admin: bool
    tabs: list[str] | None  # null = every tab
    created_at: datetime


def _to_dto(user: UserORM) -> UserDTO:
    tabs = _user_tabs(user)
    return UserDTO(
        username=user.username,
        is_admin=user.is_admin,
        tabs=None if tabs is None else list(tabs),
        created_at=user.created_at,
    )


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=2, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)
    is_admin: bool = False
    tabs: list[str] | None = None  # null = every tab


class UpdateUserRequest(BaseModel):
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_admin: bool | None = None
    tabs: list[str] | None = None  # only applied when provided
    grant_all_tabs: bool = False


@router.get("/users", response_model=list[UserDTO])
async def list_users(
    request: Request, settings: SettingsDep, session: SessionDep
) -> list[UserDTO]:
    _require_admin(request)
    repo = UserRepository(session)
    await _seed_admin_if_empty(repo, settings)
    await session.commit()
    return [_to_dto(u) for u in await repo.list_all()]


@router.post("/users", response_model=UserDTO)
async def create_user(
    body: CreateUserRequest, request: Request, settings: SettingsDep, session: SessionDep
) -> UserDTO:
    _require_admin(request)
    repo = UserRepository(session)
    await _seed_admin_if_empty(repo, settings)
    if await repo.get_by_username(body.username) is not None:
        raise HTTPException(status_code=409, detail="username already exists")
    tabs = _validate_tabs(body.tabs)
    user = await repo.create(
        username=body.username,
        password_hash=hash_password(body.password),
        is_admin=body.is_admin,
        allowed_tabs=tabs,
    )
    await session.commit()
    return _to_dto(user)


@router.patch("/users/{username}", response_model=UserDTO)
async def update_user(
    username: str,
    body: UpdateUserRequest,
    request: Request,
    settings: SettingsDep,
    session: SessionDep,
) -> UserDTO:
    _require_admin(request)
    repo = UserRepository(session)
    user = await repo.get_by_username(username)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    if body.password is not None:
        user.password_hash = hash_password(body.password)
    if body.is_admin is not None:
        if user.is_admin and not body.is_admin and await repo.admin_count() <= 1:
            raise HTTPException(status_code=400, detail="cannot demote the last admin")
        user.is_admin = body.is_admin
    if body.grant_all_tabs:
        user.allowed_tabs = tabs_to_json(None)
    elif body.tabs is not None:
        user.allowed_tabs = tabs_to_json(list(_validate_tabs(body.tabs) or ()))
    await session.commit()
    return _to_dto(user)


@router.delete("/users/{username}", response_model=OkResponse)
async def delete_user(
    username: str, request: Request, settings: SettingsDep, session: SessionDep
) -> OkResponse:
    claims = _require_admin(request)
    if claims.subject == username:
        raise HTTPException(status_code=400, detail="you cannot delete your own account")
    repo = UserRepository(session)
    user = await repo.get_by_username(username)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    if user.is_admin and await repo.admin_count() <= 1:
        raise HTTPException(status_code=400, detail="cannot delete the last admin")
    await repo.delete(user)
    await session.commit()
    return OkResponse(message=f"user {username!r} deleted")
