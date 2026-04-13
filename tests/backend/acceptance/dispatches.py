from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from app.api.v1.dispatches.models import Dispatch

pytestmark = pytest.mark.asyncio


async def test_dispatches_can_be_filtered_by_terminated(
    client: AsyncClient,
    create_execution,
    session_factory,
) -> None:
    first_execution = await create_execution(
        {
            "name": "Alpha echo",
            "spec": {"kind": "command", "command": "echo alpha"},
        }
    )
    second_execution = await create_execution(
        {
            "name": "Beta echo",
            "spec": {"kind": "command", "command": "echo beta"},
        }
    )

    first_dispatch_id = uuid4()
    second_dispatch_id = uuid4()

    async with session_factory() as session:
        session.add(
            Dispatch(
                id=first_dispatch_id,
                execution_id=UUID(first_execution["id"]),
                terminated=False,
                worker_response={"id": str(first_dispatch_id), "process_id": 111},
            )
        )
        session.add(
            Dispatch(
                id=second_dispatch_id,
                execution_id=UUID(second_execution["id"]),
                terminated=True,
                worker_response={"id": str(second_dispatch_id), "process_id": 222},
            )
        )
        await session.commit()

    response = await client.get("/api/v1/dispatches/", params={"terminated": "true", "limit": 100})

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "items": [
            {
                "id": str(second_dispatch_id),
                "created_at": response.json()["items"][0]["created_at"],
                "updated_at": response.json()["items"][0]["updated_at"],
                "execution_id": second_execution["id"],
                "terminated": True,
                "worker_response": {"id": str(second_dispatch_id), "process_id": 222},
            }
        ],
        "count": 1,
    }

    response = await client.get("/api/v1/dispatches/", params={"terminated": "false", "limit": 100})

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "items": [
            {
                "id": str(first_dispatch_id),
                "created_at": response.json()["items"][0]["created_at"],
                "updated_at": response.json()["items"][0]["updated_at"],
                "execution_id": first_execution["id"],
                "terminated": False,
                "worker_response": {"id": str(first_dispatch_id), "process_id": 111},
            }
        ],
        "count": 1,
    }
