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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a process-wide singleton of the resolved settings."""
    return Settings()
