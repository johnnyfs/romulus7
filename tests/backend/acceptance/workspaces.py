from datetime import datetime
from http import HTTPStatus

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio
WORKSPACES_PATH = "/api/v1/workspaces/"


def assert_workspace_payload(payload: dict, *, expected_name: str) -> None:
    assert payload["name"] == expected_name
    assert payload["id"]
    assert "deleted" not in payload
    assert datetime.fromisoformat(payload["created_at"])
    assert datetime.fromisoformat(payload["updated_at"])


async def test_workspace_crud_contract(
    client: AsyncClient,
    create_workspace,
) -> None:
    alpha_workspace = await create_workspace("alpha")
    beta_workspace = await create_workspace("beta")

    assert_workspace_payload(alpha_workspace, expected_name="alpha")
    assert_workspace_payload(beta_workspace, expected_name="beta")

    list_response = await client.get(WORKSPACES_PATH, params={"limit": 100})

    assert list_response.status_code == HTTPStatus.OK
    listed_payload = list_response.json()
    assert listed_payload["count"] == 2
    assert {item["id"] for item in listed_payload["items"]} == {
        alpha_workspace["id"],
        beta_workspace["id"],
    }

    get_response = await client.get(f"{WORKSPACES_PATH}{alpha_workspace['id']}")

    assert get_response.status_code == HTTPStatus.OK
    assert get_response.json() == alpha_workspace

    delete_response = await client.delete(f"{WORKSPACES_PATH}{alpha_workspace['id']}")

    assert delete_response.status_code == HTTPStatus.OK
    assert delete_response.json() == {"id": alpha_workspace["id"], "deleted": True}

    missing_after_delete_response = await client.get(
        f"{WORKSPACES_PATH}{alpha_workspace['id']}"
    )

    assert missing_after_delete_response.status_code == HTTPStatus.NOT_FOUND
    assert missing_after_delete_response.json()["detail"] == (
        f"workspace {alpha_workspace['id']} not found"
    )

    list_after_delete_response = await client.get(WORKSPACES_PATH, params={"limit": 100})

    assert list_after_delete_response.status_code == HTTPStatus.OK
    assert list_after_delete_response.json() == {
        "items": [beta_workspace],
        "count": 1,
    }
