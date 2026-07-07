"""Application configuration.

Settings are loaded from environment variables (and `.env` in development).
All secrets stay server-side; nothing here is ever exposed to the browser.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

Environment = Literal["development", "staging", "production", "test"]

# Resolve the repo root from this file's location so `.env` is found no matter
# the current working directory (running from repo root, backend/, or a tool
# like Alembic all work). config.py → mentor → src → backend → <repo root>.
_REPO_ROOT = Path(__file__).resolve().parents[3]

# Candidate env files, lowest-priority first. CWD-relative entries are kept so
# a local override (e.g. backend/.env) still wins over the repo-root file.
_ENV_FILES: tuple[str, ...] = (
    str(_REPO_ROOT / ".env"),
    str(_REPO_ROOT / ".env.local"),
    ".env",
    ".env.local",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MENTOR_",
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    env: Environment = "development"
    log_level: str = "INFO"

    api_prefix: str = "/api/v1"
    # NoDecode keeps pydantic-settings from JSON-parsing the env value so the
    # CSV splitter in `_split_csv` below can handle "a,b,c" form from .env.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "mentor"
    db_user: str = "mentor"
    db_password: SecretStr = SecretStr("change-me")
    db_echo: bool = False

    auth_username: str = "mentor"
    auth_password_hash: str = ""
    jwt_secret: SecretStr = SecretStr("please-generate-a-32-byte-secret")
    jwt_ttl_hours: int = 12

    model_store_dir: str = "models"

    # Optional: serve the built frontend (frontend/dist) from this same app so
    # a single-user deploy is one service. Empty -> auto-detect <repo>/frontend/dist.
    frontend_dist_dir: str = ""

    # --- market-data sources ---
    # Failover order: the ingester tries each in turn until one returns bars.
    # Twelve Data (keyed) first for intraday quality; Yahoo (free, no key)
    # second for redundancy and deep daily history.
    price_source_order: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["twelve_data", "yahoo"]
    )

    # --- autonomous prediction loop ---
    # When enabled, an in-process scheduler predicts on a cadence, resolves
    # due predictions, and periodically retrains + promotes the best model.
    loop_enabled: bool = False
    loop_symbol: str = "EURUSD"
    loop_timeframe: str = "1h"
    loop_horizon_bars: int = 24
    loop_predict_interval_minutes: int = 60
    loop_resolve_interval_minutes: int = 15
    loop_retrain_interval_hours: int = 168  # weekly

    # --- news sentiment (GDELT, free, no key) ---
    news_query_key: str = "eurusd"
    news_query: str = (
        '(ECB OR "European Central Bank" OR "Federal Reserve" OR "euro dollar" OR EURUSD) '
        "sourcelang:eng"
    )

    # --- external service keys ---
    # Read from their conventional, un-prefixed env var names (via
    # validation_alias) so the keys work straight from .env. SecretStr keeps
    # them out of logs and repr. The factories read these from Settings rather
    # than os.environ, so a value in .env is actually surfaced.
    llm_model: str = "claude-opus-4-8"
    anthropic_api_key: SecretStr = Field(
        default=SecretStr(""), validation_alias="ANTHROPIC_API_KEY"
    )
    twelve_data_api_key: SecretStr = Field(
        default=SecretStr(""), validation_alias="TWELVE_DATA_API_KEY"
    )
    newsapi_key: SecretStr = Field(default=SecretStr(""), validation_alias="NEWSAPI_KEY")
    finnhub_key: SecretStr = Field(default=SecretStr(""), validation_alias="FINNHUB_KEY")

    @property
    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key.get_secret_value().strip())

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def database_url(self) -> str:
        password = self.db_password.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.db_user}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def resolved_frontend_dist(self) -> Path | None:
        """The built-frontend directory to serve, if it exists."""
        p = (
            Path(self.frontend_dist_dir)
            if self.frontend_dist_dir
            else (_REPO_ROOT / "frontend" / "dist")
        )
        return p if p.is_dir() else None

    def insecure_production_reasons(self) -> list[str]:
        """Fatal security problems for a public deploy — startup refuses these.

        Empty in dev. These are the ones that leave the API open or forgeable.
        """
        if not self.is_production:
            return []
        reasons: list[str] = []
        if not self.auth_password_hash.strip():
            reasons.append("MENTOR_AUTH_PASSWORD_HASH is unset — the API would be OPEN")
        secret = self.jwt_secret.get_secret_value()
        if not secret or secret == "please-generate-a-32-byte-secret":  # noqa: S105 (placeholder)
            reasons.append("MENTOR_JWT_SECRET is unset or the default placeholder")
        elif len(secret) < 32:
            reasons.append("MENTOR_JWT_SECRET should be at least 32 characters")
        if self.db_password.get_secret_value() in ("", "change-me"):
            reasons.append("MENTOR_DB_PASSWORD is unset or the default placeholder")
        return reasons

    def production_warnings(self) -> list[str]:
        """Non-fatal hardening advice (logged, not enforced)."""
        if not self.is_production:
            return []
        warnings: list[str] = []
        if any(o == "*" or "localhost" in o for o in self.cors_origins):
            warnings.append(
                "MENTOR_CORS_ORIGINS still allows localhost/* — harmless for a "
                "same-origin deploy, but set your real origin if the frontend is separate"
            )
        return warnings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a process-wide singleton of the resolved settings."""
    return Settings()
