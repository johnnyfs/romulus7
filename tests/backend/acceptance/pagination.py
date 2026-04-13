from http import HTTPStatus

import pytest
from httpx import AsyncClient

from app.core.config import settings

pytestmark = pytest.mark.asyncio
WORKSPACES_PATH = "/api/v1/workspaces/"


async def test_workspace_list_supports_limit_and_offset(
    client: AsyncClient,
    create_workspace,
) -> None:
    for index in range(5):
        await create_workspace(f"workspace-{index}")

    full_response = await client.get(WORKSPACES_PATH, params={"limit": settings.MAX_PAGE_SIZE})
    paginated_response = await client.get(WORKSPACES_PATH, params={"limit": 2, "offset": 1})

    assert full_response.status_code == HTTPStatus.OK
    assert paginated_response.status_code == HTTPStatus.OK

    full_items = full_response.json()["items"]
    paginated_payload = paginated_response.json()

    assert paginated_payload == {
        "items": full_items[1:3],
        "count": 2,
    }


async def test_workspace_list_defaults_to_configured_page_size(
    client: AsyncClient,
    create_workspace,
) -> None:
    for index in range(settings.DEFAULT_PAGE_SIZE + 3):
        await create_workspace(f"default-page-{index}")

    default_response = await client.get(WORKSPACES_PATH)
    explicit_response = await client.get(
        WORKSPACES_PATH,
        params={"limit": settings.DEFAULT_PAGE_SIZE, "offset": 0},
    )

    assert default_response.status_code == HTTPStatus.OK
    assert explicit_response.status_code == HTTPStatus.OK
    assert default_response.json() == explicit_response.json()
    assert default_response.json()["count"] == settings.DEFAULT_PAGE_SIZE


@pytest.mark.parametrize(
    ("params", "expected_error_field"),
    [
        ({"limit": 0}, "limit"),
        ({"limit": settings.MAX_PAGE_SIZE + 1}, "limit"),
        ({"offset": -1}, "offset"),
    ],
)
async def test_workspace_list_validates_pagination_params(
    client: AsyncClient,
    params: dict[str, int],
    expected_error_field: str,
) -> None:
    response = await client.get(WORKSPACES_PATH, params=params)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert any(
        error["loc"][-1] == expected_error_field for error in response.json()["detail"]
    )
