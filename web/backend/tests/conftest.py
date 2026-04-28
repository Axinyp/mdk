import os

# Must be set before any app module is imported so pydantic-settings picks them up.
os.environ.setdefault("MDK_DEBUG", "1")

from collections.abc import AsyncIterator  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.database as _db_module  # noqa: E402
import app.main as _main_module  # noqa: E402
from app import models as _models  # noqa: E402, F401 — registers ORM classes with Base
from app.database import Base, get_db  # noqa: E402
from app.main import app, seed_admin, seed_settings  # noqa: E402

TEST_ADMIN_PASSWORD = "Admin1234!"


@pytest_asyncio.fixture
async def engine_and_maker(monkeypatch: pytest.MonkeyPatch):
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    monkeypatch.setattr(_db_module, "engine", test_engine)
    monkeypatch.setattr(_db_module, "async_session", maker)
    monkeypatch.setattr(_main_module, "async_session", maker)
    monkeypatch.setattr(
        _main_module, "_generate_bootstrap_password", lambda length=16: TEST_ADMIN_PASSWORD
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield test_engine, maker
    finally:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine_and_maker) -> AsyncIterator[AsyncSession]:
    _, maker = engine_and_maker
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def seeded_db(db_session: AsyncSession) -> None:
    await seed_admin(db_session)
    await seed_settings(db_session)


@pytest_asyncio.fixture
async def client(engine_and_maker, seeded_db) -> AsyncIterator[AsyncClient]:
    _, maker = engine_and_maker

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        async with maker() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    resp = await client.post(
        "/api/auth/login",
        json={"username": "admin", "password": TEST_ADMIN_PASSWORD},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
