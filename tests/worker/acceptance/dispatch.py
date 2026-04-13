import asyncio
import shlex
import sys
from http import HTTPStatus
from pathlib import Path
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.main import app
from common.events import DispatchEventType

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

    async def fake_start_command(command: str, cwd: Path) -> FakeProcess:
        captured["command"] = command
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
            "execution_spec": {"kind": "command", "command": "echo hello"},
            "callback": {
                "execution_id": "00000000-0000-0000-0000-000000000999",
                "execution_name": "Alpha echo",
            },
        },
    )

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    dispatch_id = UUID(payload["id"])
    expected_cwd = tmp_path / ".workspaces" / "00000000-0000-0000-0000-000000000123" / "nested/path"
    assert payload["process_id"] == 4242
    assert captured == {
        "command": "echo hello",
        "cwd": expected_cwd,
    }
    assert expected_cwd.is_dir()
    assert app.state.worker_state.commands[dispatch_id] == 4242
    assert dispatch_id in app.state.worker_state.command_tasks
    assert app.state.worker_state.callbacks[dispatch_id] == {
        "execution_id": "00000000-0000-0000-0000-000000000999",
        "execution_name": "Alpha echo",
    }

    release_harness.set()
    await asyncio.sleep(0)


async def test_dispatch_posts_stdout_lines_as_events(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured_events: list[tuple[UUID, str, dict[str, object]]] = []

    async def fake_post_dispatch_event(_, dispatch_id: UUID, event_type, payload) -> None:
        captured_events.append((dispatch_id, str(event_type), payload.model_dump(mode="json")))

    async def wait_for_completion(dispatch_id: UUID) -> None:
        for _ in range(100):
            if len(captured_events) == 4 and dispatch_id not in app.state.worker_state.command_tasks:
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
                "command": shlex.join(
                    [sys.executable, "-c", "print('alpha'); print('beta')"]
                ),
            },
            "callback": {
                "execution_id": "00000000-0000-0000-0000-000000000999",
                "execution_name": "Alpha echo",
            },
        },
    )

    assert response.status_code == HTTPStatus.OK
    dispatch_id = UUID(response.json()["id"])

    await wait_for_completion(dispatch_id)

    assert captured_events == [
        (
            dispatch_id,
            str(DispatchEventType.COMMAND_STDOUT),
            {
                "kind": "command.stdout",
                "line": "alpha",
                "callback": {
                    "execution_id": "00000000-0000-0000-0000-000000000999",
                    "execution_name": "Alpha echo",
                },
            },
        ),
        (
            dispatch_id,
            str(DispatchEventType.COMMAND_STDOUT),
            {
                "kind": "command.stdout",
                "line": "beta",
                "callback": {
                    "execution_id": "00000000-0000-0000-0000-000000000999",
                    "execution_name": "Alpha echo",
                },
            },
        ),
        (
            dispatch_id,
            str(DispatchEventType.COMMAND_EXIT),
            {
                "kind": "command.exit",
                "exit_code": 0,
                "callback": {
                    "execution_id": "00000000-0000-0000-0000-000000000999",
                    "execution_name": "Alpha echo",
                },
            },
        ),
        (
            dispatch_id,
            str(DispatchEventType.DISPATCH_TERMINATED),
            {
                "kind": "dispatch.terminated",
                "callback": {
                    "execution_id": "00000000-0000-0000-0000-000000000999",
                    "execution_name": "Alpha echo",
                },
            },
        ),
    ]
    assert dispatch_id not in app.state.worker_state.commands
    assert dispatch_id not in app.state.worker_state.command_tasks
    assert dispatch_id not in app.state.worker_state.callbacks


async def test_dispatch_rejects_non_relative_working_directory(
    client: AsyncClient,
) -> None:
    response = await client.post(
        DISPATCH_PATH,
        json={
            "sandbox_id": None,
            "working_directory": "/absolute/path",
            "execution_spec": {"kind": "command", "command": "echo hello"},
        },
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert any(
        error["loc"][-1] == "working_directory" for error in response.json()["detail"]
    )


async def test_dispatch_supports_shell_redirection(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    async def wait_for_completion(dispatch_id: UUID) -> None:
        for _ in range(100):
            if dispatch_id not in app.state.worker_state.command_tasks:
                return

            await asyncio.sleep(0.01)

        raise AssertionError("dispatch command did not finish before timeout")

    monkeypatch.chdir(tmp_path)

    response = await client.post(
        DISPATCH_PATH,
        json={
            "sandbox_id": "00000000-0000-0000-0000-000000000123",
            "working_directory": "nested/path",
            "execution_spec": {
                "kind": "command",
                "command": "echo test > proof.txt",
            },
        },
    )

    assert response.status_code == HTTPStatus.OK
    dispatch_id = UUID(response.json()["id"])

    await wait_for_completion(dispatch_id)

    expected_file = (
        tmp_path
        / ".workspaces"
        / "00000000-0000-0000-0000-000000000123"
        / "nested/path"
        / "proof.txt"
    )
    assert expected_file.read_text().strip() == "test"


async def test_dispatch_keeps_workspace_contents_after_exit(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    async def wait_for_completion(dispatch_id: UUID) -> None:
        for _ in range(100):
            if dispatch_id not in app.state.worker_state.command_tasks:
                return

            await asyncio.sleep(0.01)

        raise AssertionError("dispatch command did not finish before timeout")

    monkeypatch.chdir(tmp_path)

    response = await client.post(
        DISPATCH_PATH,
        json={
            "sandbox_id": "00000000-0000-0000-0000-000000000123",
            "working_directory": "shared/path",
            "execution_spec": {
                "kind": "command",
                "command": "echo persisted > shared.txt",
            },
        },
    )

    assert response.status_code == HTTPStatus.OK
    dispatch_id = UUID(response.json()["id"])

    await wait_for_completion(dispatch_id)

    shared_dir = (
        tmp_path
        / ".workspaces"
        / "00000000-0000-0000-0000-000000000123"
        / "shared/path"
    )
    assert shared_dir.is_dir()
    assert (shared_dir / "shared.txt").read_text().strip() == "persisted"
    assert dispatch_id not in app.state.worker_state.commands
    assert dispatch_id not in app.state.worker_state.command_tasks
    assert dispatch_id not in app.state.worker_state.callbacks
