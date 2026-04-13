from datetime import datetime
from http import HTTPStatus

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio
SANDBOXES_PATH = "/api/v1/sandboxes/"
WORKERS_PATH = "/api/v1/workers/"


async def test_worker_lease_backpopulates_worker_and_sandbox(
    client: AsyncClient,
    create_sandbox,
    create_worker,
    create_worker_lease,
) -> None:
    worker = await create_worker("http://localhost:9000/")
    sandbox = await create_sandbox("alpha")

    lease = await create_worker_lease(worker["id"], sandbox["id"])

    assert lease["worker_id"] == worker["id"]
    assert lease["sandbox_id"] == sandbox["id"]
    assert lease["sandbox_name"] == sandbox["name"]
    assert lease["id"]
    assert "deleted" not in lease
    assert datetime.fromisoformat(lease["created_at"])
    assert datetime.fromisoformat(lease["updated_at"])

    worker_response = await client.get(f"{WORKERS_PATH}{worker['id']}")

    assert worker_response.status_code == HTTPStatus.OK
    worker_payload = worker_response.json()
    assert worker_payload["leases"] == [lease]

    sandbox_response = await client.get(f"{SANDBOXES_PATH}{sandbox['id']}")

    assert sandbox_response.status_code == HTTPStatus.OK
    assert sandbox_response.json()["worker_lease_id"] == lease["id"]


async def test_worker_lease_requires_unique_worker_sandbox_combo(
    client: AsyncClient,
    create_sandbox,
    create_worker,
    create_worker_lease,
) -> None:
    worker = await create_worker("http://localhost:9000/")
    sandbox = await create_sandbox("alpha")

    await create_worker_lease(worker["id"], sandbox["id"])
    duplicate_response = await client.post(
        f"{WORKERS_PATH}{worker['id']}/lease",
        json={"sandbox_id": sandbox["id"]},
    )

    assert duplicate_response.status_code == HTTPStatus.CONFLICT
    assert duplicate_response.json()["detail"] == (
        f"worker {worker['id']} already leased to sandbox {sandbox['id']}"
    )
