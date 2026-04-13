from http import HTTPStatus

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

HEALTH_PATH = "/api/v1/health/"


async def test_health_check(client: AsyncClient) -> None:
    response = await client.get(HEALTH_PATH)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}
