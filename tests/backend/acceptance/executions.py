from datetime import datetime
from http import HTTPStatus

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio
EXECUTIONS_PATH = "/api/v1/executions/"


def assert_execution_payload(payload: dict, *, expected_commands: list[str]) -> None:
    assert payload["spec"] == {"kind": "command", "commands": expected_commands}
    assert payload["id"]
    assert "deleted" not in payload
    assert datetime.fromisoformat(payload["created_at"])
    assert datetime.fromisoformat(payload["updated_at"])


async def test_execution_crud_contract(
    client: AsyncClient,
    create_execution,
) -> None:
    alpha_execution = await create_execution({"kind": "command", "commands": ["echo", "alpha"]})
    beta_execution = await create_execution({"kind": "command", "commands": ["echo", "beta"]})

    assert_execution_payload(alpha_execution, expected_commands=["echo", "alpha"])
    assert_execution_payload(beta_execution, expected_commands=["echo", "beta"])

    list_response = await client.get(EXECUTIONS_PATH, params={"limit": 100})

    assert list_response.status_code == HTTPStatus.OK
    listed_payload = list_response.json()
    assert listed_payload["count"] == 2
    assert {item["id"] for item in listed_payload["items"]} == {
        alpha_execution["id"],
        beta_execution["id"],
    }

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
    assert list_after_delete_response.json() == {
        "items": [beta_execution],
        "count": 1,
    }
