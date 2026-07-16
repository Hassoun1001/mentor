"""Multi-user privilege plumbing — JWT claims round-trip + tabs serialization."""

from __future__ import annotations

from mentor.application.auth import AuthService, hash_password, verify_password
from mentor.config import Settings
from mentor.infrastructure.repositories.users import tabs_from_json, tabs_to_json


def _settings() -> Settings:
    return Settings(
        auth_username="mentor",
        auth_password_hash=hash_password("a strong password"),
        jwt_secret="a-test-secret-that-is-long-enough-x",
        jwt_ttl_hours=1,
        db_password="x",
    )


def test_token_carries_tabs_and_admin_flag() -> None:
    service = AuthService(_settings())
    token = service.issue_token("mohit", is_admin=False, tabs=("tips", "lessons"))
    claims = service.verify(token.access_token)
    assert claims.subject == "mohit"
    assert claims.is_admin is False
    assert claims.tabs == ("tips", "lessons")


def test_admin_token_grants_all_tabs() -> None:
    service = AuthService(_settings())
    token = service.issue_token("mentor", is_admin=True, tabs=None)
    claims = service.verify(token.access_token)
    assert claims.is_admin is True
    assert claims.tabs is None  # None == every tab


def test_legacy_token_without_privilege_claims_defaults_to_full_access() -> None:
    # Tokens minted by the pre-multi-user code had no adm/tabs keys; the
    # single account they belonged to was the admin.
    service = AuthService(_settings())
    legacy = service._issue_token()  # the legacy internal path
    claims = service.verify(legacy.access_token)
    assert claims.is_admin is True
    assert claims.tabs is None


def test_tabs_json_round_trip() -> None:
    assert tabs_from_json(tabs_to_json(None)) is None
    assert tabs_from_json(tabs_to_json(["tips", "risk", "tips"])) == ["risk", "tips"]
    assert tabs_from_json("not json") is None  # corrupt value fails open to all


def test_password_hash_round_trip() -> None:
    hashed = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong", hashed)
