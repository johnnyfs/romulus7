from http import HTTPStatus

import pytest
from httpx import AsyncClient

from conftest import HEALTH_PATH

pytestmark = pytest.mark.asyncio


async def test_health_check(client: AsyncClient) -> None:
    response = await client.get(HEALTH_PATH)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}
