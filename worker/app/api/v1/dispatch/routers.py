import asyncio
import ctypes
import logging
import os
import signal
import sys
from pathlib import Path
from uuid import UUID, uuid4

import httpx
from fastapi import FastAPI

from app.api.v1.dispatch.schemas import DispatchRequest, DispatchResponse
from app.core.config import settings
from app.core.state import worker_state
from common.events import CommandStdoutEventPayload, DispatchEventType, EventSourceType

app = FastAPI()
logger = logging.getLogger(__name__)


def _set_parent_death_signal() -> None:
    if os.name != "posix" or not sys.platform.startswith("linux"):
        return

    libc = ctypes.CDLL(None)
    pr_set_pdeathsig = 1
    libc.prctl(pr_set_pdeathsig, signal.SIGTERM)


async def start_command(
    command: str,
    cwd: Path,
) -> asyncio.subprocess.Process:
    kwargs = {"cwd": str(cwd), "stdout": asyncio.subprocess.PIPE}
    if os.name == "posix" and sys.platform.startswith("linux"):
        kwargs["preexec_fn"] = _set_parent_death_signal

    return await asyncio.create_subprocess_shell(command, **kwargs)


async def post_dispatch_event(
    client: httpx.AsyncClient,
    dispatch_id: UUID,
    line: str,
) -> None:
    callback = worker_state.callbacks.get(dispatch_id)
    response = await client.post(
        "/api/v1/events/",
        json={
            "source_type": EventSourceType.DISPATCH,
            "source_id": str(dispatch_id),
            "type": DispatchEventType.COMMAND_STDOUT,
            "payload": CommandStdoutEventPayload(
                line=line,
                callback=callback,
            ).model_dump(mode="json"),
        },
    )
    response.raise_for_status()


async def forward_command_output(
    dispatch_id: UUID,
    process: asyncio.subprocess.Process,
) -> None:
    try:
        async with httpx.AsyncClient(base_url=settings.BACKEND_URL) as client:
            if process.stdout is not None:
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break

                    try:
                        await post_dispatch_event(
                            client,
                            dispatch_id,
                            line.decode(errors="replace").rstrip("\r\n"),
                        )
                    except Exception:
                        logger.exception("Failed to post dispatch event for %s", dispatch_id)

            await process.wait()
    finally:
        worker_state.commands.pop(dispatch_id, None)
        worker_state.command_tasks.pop(dispatch_id, None)
        worker_state.callbacks.pop(dispatch_id, None)


@app.post("/")
async def dispatch(
    request: DispatchRequest,
) -> DispatchResponse:
    dispatch_id = uuid4()
    workspace_id = request.sandbox_id or dispatch_id
    workspace_dir = Path(".workspaces") / str(workspace_id)
    working_dir = workspace_dir / request.working_directory if request.working_directory else workspace_dir
    working_dir.mkdir(parents=True, exist_ok=True)
    working_dir = working_dir.resolve()

    process = await start_command(
        request.execution_spec.command,
        cwd=working_dir,
    )
    worker_state.commands[dispatch_id] = process.pid
    if request.callback is not None:
        worker_state.callbacks[dispatch_id] = request.callback
    worker_state.command_tasks[dispatch_id] = asyncio.create_task(
        forward_command_output(dispatch_id, process)
    )

    return DispatchResponse(id=dispatch_id, process_id=process.pid)
