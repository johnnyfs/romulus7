from datetime import datetime
from http import HTTPStatus

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio
WORKERS_PATH = "/api/v1/workers/"


def assert_worker_payload(payload: dict, *, expected_url: str) -> None:
    assert payload["url"] == expected_url
    assert payload["heartbeat_at"] is None
    assert payload["leases"] == []
    assert payload["id"]
    assert "deleted" not in payload
    assert datetime.fromisoformat(payload["created_at"])
    assert datetime.fromisoformat(payload["updated_at"])


async def test_worker_crud_contract(
    client: AsyncClient,
    create_worker,
) -> None:
    local_worker = await create_worker("http://localhost:9000/")
    other_worker = await create_worker("http://localhost:9001/")

    assert_worker_payload(local_worker, expected_url="http://localhost:9000/")
    assert_worker_payload(other_worker, expected_url="http://localhost:9001/")

    list_response = await client.get(WORKERS_PATH, params={"limit": 100})

    assert list_response.status_code == HTTPStatus.OK
    listed_payload = list_response.json()
    assert listed_payload["count"] == 2
    assert {item["id"] for item in listed_payload["items"]} == {
        local_worker["id"],
        other_worker["id"],
    }

    get_response = await client.get(f"{WORKERS_PATH}{local_worker['id']}")

    assert get_response.status_code == HTTPStatus.OK
    assert get_response.json() == local_worker

    delete_response = await client.delete(f"{WORKERS_PATH}{local_worker['id']}")

    assert delete_response.status_code == HTTPStatus.OK
    assert delete_response.json() == {"id": local_worker["id"], "deleted": True}

    missing_after_delete_response = await client.get(
        f"{WORKERS_PATH}{local_worker['id']}"
    )

    assert missing_after_delete_response.status_code == HTTPStatus.NOT_FOUND
    assert missing_after_delete_response.json()["detail"] == (
        f"worker {local_worker['id']} not found"
    )

    list_after_delete_response = await client.get(WORKERS_PATH, params={"limit": 100})

    assert list_after_delete_response.status_code == HTTPStatus.OK
    assert list_after_delete_response.json() == {
        "items": [other_worker],
        "count": 1,
    }


async def test_worker_heartbeat_contract(
    client: AsyncClient,
    create_worker,
) -> None:
    worker = await create_worker("http://localhost:9000/")

    heartbeat_response = await client.post(f"{WORKERS_PATH}{worker['id']}/heartbeat")

    assert heartbeat_response.status_code == HTTPStatus.OK
    heartbeat_payload = heartbeat_response.json()
    assert heartbeat_payload["id"] == worker["id"]
    assert heartbeat_payload["url"] == worker["url"]
    assert "deleted" not in heartbeat_payload
    assert datetime.fromisoformat(heartbeat_payload["created_at"])
    assert datetime.fromisoformat(heartbeat_payload["updated_at"])
    assert heartbeat_payload["heartbeat_at"] is not None
    assert datetime.fromisoformat(heartbeat_payload["heartbeat_at"])

    get_response = await client.get(f"{WORKERS_PATH}{worker['id']}")

    assert get_response.status_code == HTTPStatus.OK
    assert get_response.json() == heartbeat_payload
