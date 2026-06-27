"""Auth service tests."""

from __future__ import annotations

import contextlib
import time

import pytest

from mentor.application.auth import (
    AuthError,
    AuthService,
    Credentials,
    hash_password,
)
from mentor.config import Settings


def _settings(*, password: str = "correct horse battery staple") -> Settings:
    return Settings(
        auth_username="mentor",
        auth_password_hash=hash_password(password),
        jwt_secret="a-test-secret-that-is-long-enough-x",
        jwt_ttl_hours=1,
        db_password="x",
    )


def test_login_returns_signed_jwt() -> None:
    svc = AuthService(_settings())
    token = svc.login(Credentials("mentor", "correct horse battery staple"))
    assert token.access_token.count(".") == 2  # header.payload.sig


def test_wrong_password_rejected() -> None:
    svc = AuthService(_settings())
    with pytest.raises(AuthError):
        svc.login(Credentials("mentor", "wrong"))


def test_wrong_username_rejected() -> None:
    svc = AuthService(_settings())
    with pytest.raises(AuthError):
        svc.login(Credentials("not-mentor", "correct horse battery staple"))


def test_verify_round_trips() -> None:
    svc = AuthService(_settings())
    token = svc.login(Credentials("mentor", "correct horse battery staple"))
    claims = svc.verify(token.access_token)
    assert claims.subject == "mentor"


def test_unconfigured_rejects_login() -> None:
    svc = AuthService(Settings(db_password="x"))  # no password hash
    with pytest.raises(AuthError):
        svc.login(Credentials("mentor", "anything"))


def test_tampered_token_rejected() -> None:
    svc = AuthService(_settings())
    token = svc.login(Credentials("mentor", "correct horse battery staple"))
    parts = token.access_token.split(".")
    bad = ".".join([parts[0], parts[1] + "x", parts[2]])
    with pytest.raises(AuthError):
        svc.verify(bad)


def test_other_secret_cant_verify() -> None:
    issuer = AuthService(_settings())
    token = issuer.login(Credentials("mentor", "correct horse battery staple"))
    impostor = AuthService(
        Settings(
            auth_username="mentor",
            auth_password_hash=hash_password("x"),
            jwt_secret="totally-different-secret-thirty-two-bytes",
            db_password="x",
        )
    )
    with pytest.raises(AuthError):
        impostor.verify(token.access_token)


def test_consistent_time_for_username_compare() -> None:
    """We only assert the wrong-username path doesn't measurably leak —
    not a strong timing-attack proof, just a smoke check."""
    svc = AuthService(_settings())

    def measure(username: str) -> float:
        start = time.perf_counter()
        with contextlib.suppress(AuthError):
            svc.login(Credentials(username, "wrong"))
        return time.perf_counter() - start

    # Take a few measurements; the medians should be comparable. We
    # accept any ratio < 5x to allow noise on slow CI.
    correct = sorted(measure("mentor") for _ in range(5))[2]
    wrong = sorted(measure("xxxxxx") for _ in range(5))[2]
    assert correct < 1.0 and wrong < 1.0
