"""Async SQLAlchemy engine and session factory.

The engine is created lazily so tests and offline tools (Alembic, CLI) can
import the rest of the package without forcing a database connection.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Final

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from mentor.config import Settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


_POOL_KWARGS: Final[dict[str, object]] = {
    "pool_size": 5,
    "max_overflow": 10,
    "pool_pre_ping": True,
    "pool_recycle": 1800,
}


def build_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(
        settings.database_url,
        echo=settings.db_echo,
        future=True,
        **_POOL_KWARGS,
    )


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        engine,
        expire_on_commit=False,
        autoflush=False,
        class_=AsyncSession,
    )


@asynccontextmanager
async def session_scope(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Provide a transactional session — commit on success, rollback on error."""
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
