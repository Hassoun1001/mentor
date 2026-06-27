"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from mentor.config import Settings
from mentor.main import create_app


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    return Settings(env="test", db_password="test", jwt_secret="test-secret-for-tests-only-32b")


@pytest.fixture
async def client(test_settings: Settings) -> AsyncIterator[AsyncClient]:
    app = create_app(test_settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
