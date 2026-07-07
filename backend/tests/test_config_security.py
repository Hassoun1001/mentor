"""Production security guard — refuses insecure public deploys.

``_env_file=None`` skips env files so the developer's real .env can't mask
the assertions; fields not passed fall back to their (insecure) defaults.
"""

from __future__ import annotations

from mentor.config import Settings


def test_development_is_never_flagged() -> None:
    s = Settings(_env_file=None, env="development")
    assert s.insecure_production_reasons() == []


def test_production_defaults_are_all_flagged() -> None:
    s = Settings(_env_file=None, env="production")
    joined = " ".join(s.insecure_production_reasons())
    assert "AUTH_PASSWORD_HASH" in joined
    assert "JWT_SECRET" in joined
    assert "DB_PASSWORD" in joined
    # CORS is a non-fatal warning, not a startup blocker.
    assert any("CORS_ORIGINS" in w for w in s.production_warnings())


def test_production_secure_config_passes() -> None:
    s = Settings(
        _env_file=None,
        env="production",
        auth_password_hash="$2b$12$0123456789012345678901uABCDEFGHIJKLMNOPQRSTUV.wxyz",
        jwt_secret="x" * 40,
        db_password="a-genuinely-strong-password",
        cors_origins=["https://mentor.example.com"],
    )
    assert s.insecure_production_reasons() == []


def test_short_jwt_secret_is_flagged() -> None:
    s = Settings(
        _env_file=None,
        env="production",
        auth_password_hash="hash",
        jwt_secret="too-short",
        db_password="strong-enough",
        cors_origins=["https://x.com"],
    )
    assert any("at least 32" in r for r in s.insecure_production_reasons())
