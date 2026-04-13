import asyncio
import os
import signal
import sys
from collections.abc import AsyncIterator
from contextlib import suppress
from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("BACKEND_ORIGIN", "http://localhost")
os.environ.setdefault("BACKEND_PORT", "8000")
os.environ.setdefault("WORKER_ORIGIN", "http://localhost")
os.environ.setdefault("WORKER_PORT", "8080")
os.environ.setdefault("WORKER_HEARTBEAT_SECONDS", "5")

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKER_ROOT = REPO_ROOT / "worker"
if str(WORKER_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKER_ROOT))

from app.main import app


async def reset_worker_state() -> None:
    for process_id in list(app.state.worker_state.commands.values()):
        with suppress(ProcessLookupError):
            os.kill(process_id, signal.SIGTERM)

    tasks = list(app.state.worker_state.command_tasks.values())
    for task in tasks:
        task.cancel()

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

    app.state.worker_state.id = None
    app.state.worker_state.commands.clear()
    app.state.worker_state.command_tasks.clear()


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    await reset_worker_state()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as test_client:
        yield test_client

    await reset_worker_state()
