import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from uuid import UUID

import httpx
from fastapi import FastAPI

from app.api.v1.routers import app as api_v1
from app.core.config import settings
from app.core.state import WorkerState


logger = logging.getLogger(__name__)


async def register_worker(client: httpx.AsyncClient) -> WorkerState:
    response = await client.post("/api/v1/workers/", json={"url": settings.WORKER_URL})
    response.raise_for_status()
    payload = response.json()
    return WorkerState(id=UUID(payload["id"]))


async def send_heartbeats(
    client: httpx.AsyncClient,
    worker_state: WorkerState,
) -> None:
    while True:
        try:
            response = await client.post(f"/api/v1/workers/{worker_state.id}/heartbeat")
            response.raise_for_status()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Failed to send worker heartbeat")

        await asyncio.sleep(settings.WORKER_HEARTBEAT_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(base_url=settings.BACKEND_URL) as client:
        worker_state = await register_worker(client)
        heartbeat_task = asyncio.create_task(send_heartbeats(client, worker_state))
        app.state.worker_state = worker_state

        try:
            yield
        finally:
            heartbeat_task.cancel()
            with suppress(asyncio.CancelledError):
                await heartbeat_task

            app.state.worker_state = None


app = FastAPI(title="romulus-worker", lifespan=lifespan)
app.mount("/api/v1", api_v1)
