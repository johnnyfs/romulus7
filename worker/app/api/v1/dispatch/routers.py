import asyncio
import ctypes
import os
import signal
import sys
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI

from app.api.v1.dispatch.schemas import DispatchRequest, DispatchResponse
from app.core.state import worker_state

app = FastAPI()


def _set_parent_death_signal() -> None:
    if os.name != "posix" or not sys.platform.startswith("linux"):
        return

    libc = ctypes.CDLL(None)
    pr_set_pdeathsig = 1
    libc.prctl(pr_set_pdeathsig, signal.SIGTERM)


async def start_command(
    commands: list[str],
    cwd: Path,
) -> asyncio.subprocess.Process:
    kwargs = {"cwd": str(cwd)}
    if os.name == "posix" and sys.platform.startswith("linux"):
        kwargs["preexec_fn"] = _set_parent_death_signal

    return await asyncio.create_subprocess_exec(*commands, **kwargs)


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
        request.execution_spec.commands,
        cwd=working_dir,
    )
    worker_state.commands[dispatch_id] = process.pid

    return DispatchResponse(id=dispatch_id, process_id=process.pid)
