import asyncio
import sys
from http import HTTPStatus
from pathlib import Path
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.main import app

pytestmark = pytest.mark.asyncio

DISPATCH_PATH = "/api/v1/dispatch/"


class FakeProcess:
    def __init__(self, pid: int):
        self.pid = pid
        self.stdout = None

    async def wait(self) -> int:
        return 0


async def test_dispatch_runs_command_in_workspace_directory(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}
    release_harness = asyncio.Event()

    async def fake_start_command(commands: list[str], cwd: Path) -> FakeProcess:
        captured["commands"] = commands
        captured["cwd"] = cwd
        return FakeProcess(pid=4242)

    async def fake_forward_command_output(dispatch_id: UUID, process: FakeProcess) -> None:
        await release_harness.wait()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("app.api.v1.dispatch.routers.start_command", fake_start_command)
    monkeypatch.setattr(
        "app.api.v1.dispatch.routers.forward_command_output",
        fake_forward_command_output,
    )

    response = await client.post(
        DISPATCH_PATH,
        json={
            "sandbox_id": "00000000-0000-0000-0000-000000000123",
            "working_directory": "nested/path",
            "execution_spec": {"kind": "command", "commands": ["echo", "hello"]},
        },
    )

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    dispatch_id = UUID(payload["id"])
    expected_cwd = tmp_path / ".workspaces" / "00000000-0000-0000-0000-000000000123" / "nested/path"
    assert payload["process_id"] == 4242
    assert captured == {
        "commands": ["echo", "hello"],
        "cwd": expected_cwd,
    }
    assert expected_cwd.is_dir()
    assert app.state.worker_state.commands[dispatch_id] == 4242
    assert dispatch_id in app.state.worker_state.command_tasks

    release_harness.set()
    await asyncio.sleep(0)


async def test_dispatch_posts_stdout_lines_as_events(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured_events: list[tuple[UUID, str]] = []

    async def fake_post_dispatch_event(_, dispatch_id: UUID, line: str) -> None:
        captured_events.append((dispatch_id, line))

    async def wait_for_completion(dispatch_id: UUID) -> None:
        for _ in range(100):
            if len(captured_events) == 2 and dispatch_id not in app.state.worker_state.command_tasks:
                return

            await asyncio.sleep(0.01)

        raise AssertionError("dispatch stdout events were not forwarded before timeout")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "app.api.v1.dispatch.routers.post_dispatch_event",
        fake_post_dispatch_event,
    )

    response = await client.post(
        DISPATCH_PATH,
        json={
            "sandbox_id": None,
            "working_directory": None,
            "execution_spec": {
                "kind": "command",
                "commands": [
                    sys.executable,
                    "-c",
                    "print('alpha'); print('beta')",
                ],
            },
        },
    )

    assert response.status_code == HTTPStatus.OK
    dispatch_id = UUID(response.json()["id"])

    await wait_for_completion(dispatch_id)

    assert captured_events == [
        (dispatch_id, "alpha"),
        (dispatch_id, "beta"),
    ]
    assert dispatch_id not in app.state.worker_state.commands
    assert dispatch_id not in app.state.worker_state.command_tasks


async def test_dispatch_rejects_non_relative_working_directory(
    client: AsyncClient,
) -> None:
    response = await client.post(
        DISPATCH_PATH,
        json={
            "sandbox_id": None,
            "working_directory": "/absolute/path",
            "execution_spec": {"kind": "command", "commands": ["echo", "hello"]},
        },
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert any(
        error["loc"][-1] == "working_directory" for error in response.json()["detail"]
    )
