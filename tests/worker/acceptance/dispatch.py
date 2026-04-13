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


async def test_dispatch_runs_command_in_workspace_directory(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}

    async def fake_start_command(commands: list[str], cwd: Path) -> FakeProcess:
        captured["commands"] = commands
        captured["cwd"] = cwd
        return FakeProcess(pid=4242)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("app.api.v1.dispatch.routers.start_command", fake_start_command)

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
