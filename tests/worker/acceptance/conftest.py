import os
import sys
from collections.abc import AsyncIterator
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


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as test_client:
        yield test_client
