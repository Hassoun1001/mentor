"""'Remember me' sign-in — token lifetime, its hard cap, and unchanged validation."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt

from mentor.api import deps
from mentor.api.v1 import auth as auth_api
from mentor.application.auth import (
    JWT_REMEMBER_TTL_MAX_DAYS,
    AuthError,
    AuthService,
    hash_password,
)
from mentor.config import Settings
from mentor.infrastructure.repositories.users import tabs_to_json
from mentor.main import create_app

_PASSWORD = "correct horse battery staple"
_SECRET = "a-test-secret-that-is-long-enough-x"
_SLACK = timedelta(seconds=5)


def _settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "env": "test",
        "auth_username": "mentor",
        "auth_password_hash": hash_password(_PASSWORD),
        "jwt_secret": _SECRET,
        "jwt_ttl_hours": 12,
        "db_password": "x",
    }
    values.update(overrides)
    return Settings(**values)


def _assert_lifetime(expires_at: datetime, expected: timedelta) -> None:
    remaining = expires_at - datetime.now(UTC)
    assert expected - _SLACK <= remaining <= expected + _SLACK


# ---------- AuthService ----------


def test_default_sign_in_keeps_the_short_lifetime() -> None:
    service = AuthService(_settings())
    _assert_lifetime(service.issue_token("mentor").expires_at, timedelta(hours=12))
    _assert_lifetime(
        service.issue_token("mentor", remember_me=False).expires_at, timedelta(hours=12)
    )


def test_remember_me_issues_the_long_lifetime() -> None:
    service = AuthService(_settings())
    token = service.issue_token("mentor", remember_me=True)
    _assert_lifetime(token.expires_at, timedelta(days=30))
    claims = service.verify(token.access_token)
    _assert_lifetime(claims.expires_at, timedelta(days=30))


def test_remember_me_lifetime_follows_the_setting() -> None:
    service = AuthService(_settings(jwt_remember_ttl_days=7))
    _assert_lifetime(service.issue_token("mentor", remember_me=True).expires_at, timedelta(days=7))


def test_remember_me_lifetime_is_hard_capped() -> None:
    service = AuthService(_settings(jwt_remember_ttl_days=365))
    token = service.issue_token("mentor", remember_me=True)
    _assert_lifetime(token.expires_at, timedelta(days=JWT_REMEMBER_TTL_MAX_DAYS))


def test_remember_me_setting_rejects_non_positive_days() -> None:
    with pytest.raises(ValueError, match="jwt_remember_ttl_days"):
        _settings(jwt_remember_ttl_days=0)


def test_remember_me_token_keeps_privileges() -> None:
    service = AuthService(_settings())
    token = service.issue_token("guest", is_admin=False, tabs=("tips",), remember_me=True)
    claims = service.verify(token.access_token)
    assert (claims.subject, claims.is_admin, claims.tabs) == ("guest", False, ("tips",))


def test_remember_me_token_still_rejected_under_another_secret() -> None:
    token = AuthService(_settings()).issue_token("mentor", remember_me=True)
    impostor = AuthService(_settings(jwt_secret="a-rotated-secret-that-is-long-enough"))
    with pytest.raises(AuthError):
        impostor.verify(token.access_token)


def test_expired_long_lived_token_rejected() -> None:
    # A 30-day token issued 31 days ago: `exp` is still enforced.
    expired = jwt.encode(
        {
            "iss": "mentor",
            "sub": "mentor",
            "iat": int((datetime.now(UTC) - timedelta(days=31)).timestamp()),
            "exp": int((datetime.now(UTC) - timedelta(days=1)).timestamp()),
        },
        _SECRET,
        algorithm="HS256",
    )
    with pytest.raises(AuthError):
        AuthService(_settings()).verify(expired)


# ---------- /auth endpoints ----------


class _FakeUsers:
    """Stands in for UserRepository so the login route runs without Postgres."""

    def __init__(self, _session: object) -> None:
        self._user = SimpleNamespace(
            username="mentor",
            password_hash=hash_password(_PASSWORD),
            is_admin=True,
            allowed_tabs=tabs_to_json(None),
        )

    async def count(self) -> int:
        return 1

    async def get_by_username(self, username: str) -> SimpleNamespace | None:
        return self._user if username == "mentor" else None


class _FakeSession:
    async def commit(self) -> None:
        return None


@pytest.fixture
async def auth_client(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncClient]:
    monkeypatch.setattr(auth_api, "UserRepository", _FakeUsers)
    monkeypatch.setattr(auth_api, "_login_attempts", {})

    async def _session() -> AsyncIterator[_FakeSession]:
        yield _FakeSession()

    app = create_app(_settings())
    app.dependency_overrides[deps.get_session] = _session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def _login(client: AsyncClient, **extra: Any) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/auth/login", json={"username": "mentor", "password": _PASSWORD, **extra}
    )
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


async def test_login_without_remember_me_is_short_lived(auth_client: AsyncClient) -> None:
    body = await _login(auth_client)
    _assert_lifetime(datetime.fromisoformat(body["expires_at"]), timedelta(hours=12))


async def test_login_with_remember_me_false_is_short_lived(auth_client: AsyncClient) -> None:
    body = await _login(auth_client, remember_me=False)
    _assert_lifetime(datetime.fromisoformat(body["expires_at"]), timedelta(hours=12))


async def test_login_with_remember_me_is_long_lived(auth_client: AsyncClient) -> None:
    body = await _login(auth_client, remember_me=True)
    _assert_lifetime(datetime.fromisoformat(body["expires_at"]), timedelta(days=30))

    me = await auth_client.get(
        "/api/v1/auth/me", headers={"authorization": f"Bearer {body['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["username"] == "mentor"


async def test_remember_me_does_not_bypass_the_password(auth_client: AsyncClient) -> None:
    response = await auth_client.post(
        "/api/v1/auth/login",
        json={"username": "mentor", "password": "wrong", "remember_me": True},
    )
    assert response.status_code == 401


async def test_protected_routes_still_need_a_valid_token(auth_client: AsyncClient) -> None:
    assert (await auth_client.get("/api/v1/auth/me")).status_code == 401
    bad = await auth_client.get("/api/v1/auth/me", headers={"authorization": "Bearer nope"})
    assert bad.status_code == 401


async def test_login_rate_limit_still_applies_with_remember_me(auth_client: AsyncClient) -> None:
    statuses = [
        (
            await auth_client.post(
                "/api/v1/auth/login",
                json={"username": "mentor", "password": "wrong", "remember_me": True},
            )
        ).status_code
        for _ in range(11)
    ]
    assert statuses[:10] == [401] * 10
    assert statuses[10] == 429


async def test_status_reports_remember_me_days(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/auth/status")
    assert response.status_code == 200
    assert response.json() == {"auth_enabled": True, "remember_me_days": 30}
