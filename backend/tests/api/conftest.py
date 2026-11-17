"""API tests run against a real PostgreSQL test database.

Set TEST_DATABASE_URL (an owner-role URL). The fixture creates the database if
needed, applies the migrations and the seed, and empties the profile tables
before each test. Without TEST_DATABASE_URL these tests are skipped; run them
with `docker compose --profile test run --rm api-test` from the deployment folder.
"""

import asyncio
import os
from collections.abc import AsyncIterator

import asyncpg
import pytest
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from app.config import Settings
from app.main import create_app
from app.seed import seed

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
INTERNAL_TOKEN = "test-internal-token-123456"


async def _ensure_database(url: str) -> None:
    parsed = make_url(url)
    conn = await asyncpg.connect(
        user=parsed.username,
        password=parsed.password,
        host=parsed.host,
        port=parsed.port or 5432,
        database="postgres",
    )
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", parsed.database)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{parsed.database}"')
    finally:
        await conn.close()


@pytest.fixture(scope="session")
async def database() -> str:
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL is not set; run the API tests through docker compose")
    await _ensure_database(TEST_DATABASE_URL)
    config = Config("alembic.ini")
    config.attributes["database_url"] = TEST_DATABASE_URL
    config.attributes["configure_logger"] = False
    # Alembic's env.py calls asyncio.run, so run it outside this event loop.
    await asyncio.to_thread(command.upgrade, config, "head")
    await seed(TEST_DATABASE_URL)
    return TEST_DATABASE_URL


def make_settings(url: str, **overrides) -> Settings:
    values = {
        "database_url": url,
        "internal_token": INTERNAL_TOKEN,
        "rate_limit_enabled": False,
        "log_level": "WARNING",
    }
    values.update(overrides)
    return Settings(**values)


@pytest.fixture
async def clean(database: str) -> None:
    engine = create_async_engine(database)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE profiles, shortlist_entries"))
    await engine.dispose()


@pytest.fixture
def app_factory(database: str):
    def factory(**overrides):
        return create_app(make_settings(database, **overrides))

    return factory


async def _client(app) -> AsyncIterator[AsyncClient]:
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
            yield client


@pytest.fixture
async def client(clean, app_factory) -> AsyncIterator[AsyncClient]:
    async for c in _client(app_factory()):
        yield c


@pytest.fixture
def client_for():
    """Build a client for an app with custom settings."""
    return _client
