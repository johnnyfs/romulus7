from http import HTTPStatus
from uuid import uuid4

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio
EVENTS_PATH = "/api/v1/events/"


async def test_event_contract_supports_source_and_since_filters(
    client: AsyncClient,
    create_event,
) -> None:
    first_source_id = str(uuid4())
    second_source_id = str(uuid4())

    first_event = await create_event(
        {
            "source_type": "dispatch",
            "source_id": first_source_id,
            "type": "command.stdout",
            "payload": {
                "kind": "command.stdout",
                "line": "alpha",
                "callback": {
                    "execution_id": "00000000-0000-0000-0000-000000000111",
                    "execution_name": "Alpha echo",
                },
            },
        }
    )
    second_event = await create_event(
        {
            "source_type": "dispatch",
            "source_id": first_source_id,
            "type": "command.stdout",
            "payload": {
                "kind": "command.stdout",
                "line": "beta",
                "callback": {
                    "execution_id": "00000000-0000-0000-0000-000000000111",
                    "execution_name": "Alpha echo",
                },
            },
        }
    )
    third_event = await create_event(
        {
            "source_type": "dispatch",
            "source_id": second_source_id,
            "type": "command.stdout",
            "payload": {
                "kind": "command.stdout",
                "line": "gamma",
                "callback": {
                    "execution_id": "00000000-0000-0000-0000-000000000222",
                    "execution_name": "Beta echo",
                },
            },
        }
    )

    assert first_event["id"] < second_event["id"] < third_event["id"]

    filtered_response = await client.get(
        EVENTS_PATH,
        params={
            "source_type": "dispatch",
            "source_id": first_source_id,
            "limit": 100,
        },
    )

    assert filtered_response.status_code == HTTPStatus.OK
    assert filtered_response.json() == {
        "items": [first_event, second_event],
        "count": 2,
    }

    since_response = await client.get(
        EVENTS_PATH,
        params={
            "source_type": "dispatch",
            "source_id": first_source_id,
            "since": first_event["id"],
            "limit": 100,
        },
    )

    assert since_response.status_code == HTTPStatus.OK
    assert since_response.json() == {
        "items": [second_event],
        "count": 1,
    }


async def test_event_contract_rejects_invalid_payload_discriminator(
    client: AsyncClient,
) -> None:
    response = await client.post(
        EVENTS_PATH,
        json={
            "source_type": "dispatch",
            "source_id": str(uuid4()),
            "type": "command.stdout",
            "payload": {
                "kind": "system.message",
                "line": "alpha",
            },
        },
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert any(error["loc"][-1] == "payload" for error in response.json()["detail"])
