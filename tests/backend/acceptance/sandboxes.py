from datetime import datetime
from http import HTTPStatus

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio
SANDBOXES_PATH = "/api/v1/sandboxes/"


def assert_sandbox_payload(payload: dict, *, expected_name: str) -> None:
    assert payload["name"] == expected_name
    assert payload["worker_lease_id"] is None
    assert payload["id"]
    assert "deleted" not in payload
    assert datetime.fromisoformat(payload["created_at"])
    assert datetime.fromisoformat(payload["updated_at"])


async def test_sandbox_crud_contract(
    client: AsyncClient,
    create_sandbox,
) -> None:
    alpha_sandbox = await create_sandbox("alpha")
    beta_sandbox = await create_sandbox("beta")

    assert_sandbox_payload(alpha_sandbox, expected_name="alpha")
    assert_sandbox_payload(beta_sandbox, expected_name="beta")

    list_response = await client.get(SANDBOXES_PATH, params={"limit": 100})

    assert list_response.status_code == HTTPStatus.OK
    listed_payload = list_response.json()
    assert listed_payload["count"] == 2
    assert {item["id"] for item in listed_payload["items"]} == {
        alpha_sandbox["id"],
        beta_sandbox["id"],
    }

    get_response = await client.get(f"{SANDBOXES_PATH}{alpha_sandbox['id']}")

    assert get_response.status_code == HTTPStatus.OK
    assert get_response.json() == alpha_sandbox

    delete_response = await client.delete(f"{SANDBOXES_PATH}{alpha_sandbox['id']}")

    assert delete_response.status_code == HTTPStatus.OK
    assert delete_response.json() == {"id": alpha_sandbox["id"], "deleted": True}

    missing_after_delete_response = await client.get(
        f"{SANDBOXES_PATH}{alpha_sandbox['id']}"
    )

    assert missing_after_delete_response.status_code == HTTPStatus.NOT_FOUND
    assert missing_after_delete_response.json()["detail"] == (
        f"sandbox {alpha_sandbox['id']} not found"
    )

    list_after_delete_response = await client.get(SANDBOXES_PATH, params={"limit": 100})

    assert list_after_delete_response.status_code == HTTPStatus.OK
    assert list_after_delete_response.json() == {
        "items": [beta_sandbox],
        "count": 1,
    }
