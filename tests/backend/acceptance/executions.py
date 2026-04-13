from datetime import datetime
from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlmodel import select

from app.api.v1.dispatches.models import Dispatch
from app.api.v1.events.models import Event

pytestmark = pytest.mark.asyncio
EXECUTIONS_PATH = "/api/v1/executions/"


def assert_execution_payload(payload: dict, *, expected_name: str, expected_command: str) -> None:
    assert payload["name"] == expected_name
    assert payload["spec"] == {"kind": "command", "command": expected_command}
    assert payload["id"]
    assert "deleted" not in payload
    assert datetime.fromisoformat(payload["created_at"])
    assert datetime.fromisoformat(payload["updated_at"])


async def test_execution_crud_contract(
    client: AsyncClient,
    create_execution,
) -> None:
    alpha_execution = await create_execution(
        {
            "name": "  Alpha echo  ",
            "spec": {"kind": "command", "command": "  echo alpha  "},
        }
    )
    beta_execution = await create_execution(
        {
            "name": "Beta echo",
            "spec": {"kind": "command", "command": "echo beta"},
        }
    )

    assert_execution_payload(
        alpha_execution,
        expected_name="Alpha echo",
        expected_command="echo alpha",
    )
    assert_execution_payload(
        beta_execution,
        expected_name="Beta echo",
        expected_command="echo beta",
    )

    list_response = await client.get(EXECUTIONS_PATH, params={"limit": 100})

    assert list_response.status_code == HTTPStatus.OK
    listed_payload = list_response.json()
    assert listed_payload["count"] == 2
    assert {item["id"] for item in listed_payload["items"]} == {
        alpha_execution["id"],
        beta_execution["id"],
    }
    for item in listed_payload["items"]:
        assert item["dispatch_id"] is None

    get_response = await client.get(f"{EXECUTIONS_PATH}{alpha_execution['id']}")

    assert get_response.status_code == HTTPStatus.OK
    assert get_response.json() == alpha_execution

    delete_response = await client.delete(f"{EXECUTIONS_PATH}{alpha_execution['id']}")

    assert delete_response.status_code == HTTPStatus.OK
    assert delete_response.json() == {"id": alpha_execution["id"], "deleted": True}

    missing_after_delete_response = await client.get(
        f"{EXECUTIONS_PATH}{alpha_execution['id']}"
    )

    assert missing_after_delete_response.status_code == HTTPStatus.NOT_FOUND
    assert missing_after_delete_response.json()["detail"] == (
        f"execution {alpha_execution['id']} not found"
    )

    list_after_delete_response = await client.get(EXECUTIONS_PATH, params={"limit": 100})

    assert list_after_delete_response.status_code == HTTPStatus.OK
    remaining = list_after_delete_response.json()
    assert remaining["count"] == 1
    assert remaining["items"][0]["id"] == beta_execution["id"]
    assert remaining["items"][0]["dispatch_id"] is None


async def test_execution_contract_rejects_blank_name(
    client: AsyncClient,
) -> None:
    response = await client.post(
        EXECUTIONS_PATH,
        json={
            "name": "   ",
            "spec": {"kind": "command", "command": "echo alpha"},
        },
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert any(error["loc"][-1] == "name" for error in response.json()["detail"])


async def test_execution_contract_rejects_blank_command(
    client: AsyncClient,
) -> None:
    response = await client.post(
        EXECUTIONS_PATH,
        json={
            "name": "Alpha echo",
            "spec": {"kind": "command", "command": "   "},
        },
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert any(error["loc"][-1] == "command" for error in response.json()["detail"])


async def test_execution_dispatch_uses_existing_worker_lease(
    client: AsyncClient,
    create_execution,
    create_sandbox,
    create_worker,
    create_worker_lease,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    execution = await create_execution(
        {
            "name": "Alpha echo",
            "spec": {"kind": "command", "command": "echo alpha"},
        }
    )
    sandbox = await create_sandbox("alpha")
    worker = await create_worker("http://localhost:9000/")
    await create_worker_lease(worker["id"], sandbox["id"])

    captured: dict[str, object] = {}
    worker_dispatch_id = str(uuid4())

    async def fake_dispatch_to_worker(worker_url: str, payload: dict) -> dict:
        captured["worker_url"] = worker_url
        captured["payload"] = payload
        return {"id": worker_dispatch_id, "process_id": 4242}

    monkeypatch.setattr(
        "app.api.v1.executions.routers.dispatch_to_worker",
        fake_dispatch_to_worker,
    )

    callback = {
        "execution_id": execution["id"],
        "execution_name": execution["name"],
    }
    response = await client.post(
        f"{EXECUTIONS_PATH}{execution['id']}/dispatch",
        json={
            "sandbox_id": sandbox["id"],
            "working_directory": "nested/path",
            "callback": callback,
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()["id"] == worker_dispatch_id
    assert response.json()["execution_id"] == execution["id"]
    assert response.json()["terminated"] is False
    assert response.json()["worker_response"] == {"id": worker_dispatch_id, "process_id": 4242}
    assert captured == {
        "worker_url": worker["url"],
        "payload": {
            "sandbox_id": sandbox["id"],
            "working_directory": "nested/path",
            "execution_spec": execution["spec"],
            "callback": callback,
        },
    }


async def test_execution_dispatch_auto_leases_worker_for_sandbox(
    client: AsyncClient,
    create_execution,
    create_sandbox,
    create_worker,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    execution = await create_execution(
        {
            "name": "Alpha echo",
            "spec": {"kind": "command", "command": "echo alpha"},
        }
    )
    sandbox = await create_sandbox("alpha")
    worker = await create_worker("http://localhost:9000/")
    worker_dispatch_id = str(uuid4())

    callback = {
        "execution_id": execution["id"],
        "execution_name": execution["name"],
    }

    async def fake_dispatch_to_worker(worker_url: str, payload: dict) -> dict:
        assert worker_url == worker["url"]
        assert payload == {
            "sandbox_id": sandbox["id"],
            "working_directory": None,
            "execution_spec": execution["spec"],
            "callback": callback,
        }
        return {"id": worker_dispatch_id, "process_id": 4242}

    monkeypatch.setattr(
        "app.api.v1.executions.routers.dispatch_to_worker",
        fake_dispatch_to_worker,
    )

    response = await client.post(
        f"{EXECUTIONS_PATH}{execution['id']}/dispatch",
        json={"sandbox_id": sandbox["id"], "working_directory": None, "callback": callback},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()["id"] == worker_dispatch_id
    assert response.json()["terminated"] is False

    worker_response = await client.get(f"/api/v1/workers/{worker['id']}")
    sandbox_response = await client.get(f"/api/v1/sandboxes/{sandbox['id']}")

    assert worker_response.status_code == HTTPStatus.OK
    assert sandbox_response.status_code == HTTPStatus.OK
    assert len(worker_response.json()["leases"]) == 1
    assert worker_response.json()["leases"][0]["sandbox_id"] == sandbox["id"]
    assert sandbox_response.json()["worker_lease_id"] == worker_response.json()["leases"][0]["id"]


async def test_execution_dispatch_validates_relative_working_directory(
    client: AsyncClient,
    create_execution,
    create_worker,
) -> None:
    execution = await create_execution(
        {
            "name": "Alpha echo",
            "spec": {"kind": "command", "command": "echo alpha"},
        }
    )
    await create_worker("http://localhost:9000/")

    response = await client.post(
        f"{EXECUTIONS_PATH}{execution['id']}/dispatch",
        json={"sandbox_id": None, "working_directory": "/absolute/path"},
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert any(
        error["loc"][-1] == "working_directory" for error in response.json()["detail"]
    )


async def test_execution_delete_cascades_to_dispatches_and_events(
    client: AsyncClient,
    create_execution,
    create_worker,
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    execution = await create_execution(
        {
            "name": "Alpha echo",
            "spec": {"kind": "command", "command": "echo alpha"},
        }
    )
    await create_worker("http://localhost:9000/")
    worker_dispatch_id = str(uuid4())

    async def fake_dispatch_to_worker(worker_url: str, payload: dict) -> dict:
        return {"id": worker_dispatch_id, "process_id": 4242}

    monkeypatch.setattr(
        "app.api.v1.executions.routers.dispatch_to_worker",
        fake_dispatch_to_worker,
    )

    dispatch_response = await client.post(
        f"{EXECUTIONS_PATH}{execution['id']}/dispatch",
        json={"sandbox_id": None, "working_directory": None},
    )
    assert dispatch_response.status_code == HTTPStatus.OK

    event_response = await client.post(
        "/api/v1/events/",
        json={
            "source_type": "dispatch",
            "source_id": worker_dispatch_id,
            "type": "command.stdout",
            "payload": {"kind": "command.stdout", "line": "alpha"},
        },
    )
    assert event_response.status_code == HTTPStatus.OK

    delete_response = await client.delete(f"{EXECUTIONS_PATH}{execution['id']}")
    assert delete_response.status_code == HTTPStatus.OK
    assert delete_response.json() == {"id": execution["id"], "deleted": True}

    events_response = await client.get(
        "/api/v1/events/",
        params={"source_type": "dispatch", "source_id": worker_dispatch_id, "limit": 100},
    )
    assert events_response.status_code == HTTPStatus.OK
    assert events_response.json() == {"items": [], "count": 0}

    async with session_factory() as session:
        dispatch = (
            await session.exec(select(Dispatch).where(Dispatch.id == UUID(worker_dispatch_id)))
        ).one()
        event = (await session.exec(select(Event).where(Event.source_id == UUID(worker_dispatch_id)))).one()

    assert dispatch.deleted is True
    assert event.deleted is True


async def test_dispatch_terminated_event_marks_dispatch_terminated(
    client: AsyncClient,
    create_execution,
    create_worker,
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    execution = await create_execution(
        {
            "name": "Alpha echo",
            "spec": {"kind": "command", "command": "echo alpha"},
        }
    )
    await create_worker("http://localhost:9000/")
    worker_dispatch_id = str(uuid4())

    async def fake_dispatch_to_worker(worker_url: str, payload: dict) -> dict:
        return {"id": worker_dispatch_id, "process_id": 4242}

    monkeypatch.setattr(
        "app.api.v1.executions.routers.dispatch_to_worker",
        fake_dispatch_to_worker,
    )

    dispatch_response = await client.post(
        f"{EXECUTIONS_PATH}{execution['id']}/dispatch",
        json={"sandbox_id": None, "working_directory": None},
    )
    assert dispatch_response.status_code == HTTPStatus.OK
    assert dispatch_response.json()["terminated"] is False

    event_response = await client.post(
        "/api/v1/events/",
        json={
            "source_type": "dispatch",
            "source_id": worker_dispatch_id,
            "type": "dispatch.terminated",
            "payload": {"kind": "dispatch.terminated"},
        },
    )
    assert event_response.status_code == HTTPStatus.OK

    async with session_factory() as session:
        dispatch = (
            await session.exec(select(Dispatch).where(Dispatch.id == UUID(worker_dispatch_id)))
        ).one()

    assert dispatch.terminated is True
