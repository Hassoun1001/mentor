"""User accounts repository."""

from __future__ import annotations

import json
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mentor.infrastructure.models import UserORM

ALL_TABS_SENTINEL = "*"


def tabs_to_json(tabs: Sequence[str] | None) -> str:
    """None means every tab (stored as the '*' sentinel)."""
    if tabs is None:
        return ALL_TABS_SENTINEL
    return json.dumps(sorted(set(tabs)))


def tabs_from_json(raw: str) -> list[str] | None:
    """None means every tab."""
    if raw.strip() == ALL_TABS_SENTINEL:
        return None
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    return [str(t) for t in data] if isinstance(data, list) else None


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(UserORM))
        return int(result.scalar_one())

    async def get_by_username(self, username: str) -> UserORM | None:
        stmt = select(UserORM).where(UserORM.username == username)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> Sequence[UserORM]:
        result = await self._session.execute(select(UserORM).order_by(UserORM.username))
        return result.scalars().all()

    async def create(
        self,
        *,
        username: str,
        password_hash: str,
        is_admin: bool = False,
        allowed_tabs: Sequence[str] | None = None,
    ) -> UserORM:
        user = UserORM(
            username=username,
            password_hash=password_hash,
            is_admin=is_admin,
            allowed_tabs=tabs_to_json(allowed_tabs),
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def admin_count(self) -> int:
        stmt = select(func.count()).select_from(UserORM).where(UserORM.is_admin.is_(True))
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def delete(self, user: UserORM) -> None:
        await self._session.delete(user)
        await self._session.flush()
