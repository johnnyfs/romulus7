import os
import sys
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path
from typing import Any

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASS", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "test")

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api.v1.executions.routers import app as executions_app
from app.api.v1.events.routers import app as events_app
from app.api.v1.events.notify_bus import PgNotifyBus
from app.api.v1.sandboxes.routers import app as sandboxes_app
from app.api.v1.workers.routers import app as workers_app
from app.api.v1.workspaces.routers import app as workspaces_app
from app.core.db import get_session
from app.main import app


EVENTS_PATH = "/api/v1/events/"
EXECUTIONS_PATH = "/api/v1/executions/"
HEALTH_PATH = "/api/v1/health/"
SANDBOXES_PATH = "/api/v1/sandboxes/"
WORKERS_PATH = "/api/v1/workers/"
WORKSPACES_PATH = "/api/v1/workspaces/"


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(engine: AsyncEngine) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.drop_all)
        await connection.run_sync(SQLModel.metadata.create_all)

    yield async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@pytest_asyncio.fixture
async def client(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    notify_bus = PgNotifyBus(dsn=None, channel="test_events_channel")

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    executions_app.dependency_overrides[get_session] = override_get_session
    events_app.dependency_overrides[get_session] = override_get_session
    sandboxes_app.dependency_overrides[get_session] = override_get_session
    workers_app.dependency_overrides[get_session] = override_get_session
    workspaces_app.dependency_overrides[get_session] = override_get_session
    events_app.state.event_notify_bus = notify_bus
    events_app.state.event_session_factory = session_factory

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as test_client:
        yield test_client

    await notify_bus.close()
    app.dependency_overrides.clear()
    executions_app.dependency_overrides.clear()
    events_app.dependency_overrides.clear()
    sandboxes_app.dependency_overrides.clear()
    workers_app.dependency_overrides.clear()
    workspaces_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def create_workspace(
    client: AsyncClient,
) -> Callable[[str], Awaitable[dict[str, Any]]]:
    async def _create_workspace(name: str) -> dict[str, Any]:
        response = await client.post(WORKSPACES_PATH, json={"name": name})
        assert response.status_code == 200, response.text
        return response.json()

    return _create_workspace


@pytest_asyncio.fixture
async def create_sandbox(
    client: AsyncClient,
) -> Callable[[str], Awaitable[dict[str, Any]]]:
    async def _create_sandbox(name: str) -> dict[str, Any]:
        response = await client.post(SANDBOXES_PATH, json={"name": name})
        assert response.status_code == 200, response.text
        return response.json()

    return _create_sandbox


@pytest_asyncio.fixture
async def create_worker(
    client: AsyncClient,
) -> Callable[[str], Awaitable[dict[str, Any]]]:
    async def _create_worker(url: str) -> dict[str, Any]:
        response = await client.post(
            WORKERS_PATH,
            json={"url": url},
        )
        assert response.status_code == 200, response.text
        return response.json()

    return _create_worker


@pytest_asyncio.fixture
async def create_execution(
    client: AsyncClient,
) -> Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]:
    async def _create_execution(execution: dict[str, Any]) -> dict[str, Any]:
        response = await client.post(
            EXECUTIONS_PATH,
            json=execution,
        )
        assert response.status_code == 200, response.text
        return response.json()

    return _create_execution


@pytest_asyncio.fixture
async def create_event(
    client: AsyncClient,
) -> Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]:
    async def _create_event(event: dict[str, Any]) -> dict[str, Any]:
        response = await client.post(
            EVENTS_PATH,
            json=event,
        )
        assert response.status_code == 200, response.text
        return response.json()

    return _create_event


@pytest_asyncio.fixture
async def create_worker_lease(
    client: AsyncClient,
) -> Callable[[str, str], Awaitable[dict[str, Any]]]:
    async def _create_worker_lease(worker_id: str, sandbox_id: str) -> dict[str, Any]:
        response = await client.post(
            f"{WORKERS_PATH}{worker_id}/lease",
            json={"sandbox_id": sandbox_id},
        )
        assert response.status_code == 200, response.text
        return response.json()

    return _create_worker_lease
