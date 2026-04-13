from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.core.schemas import BaseListItem, BaseListResponse, BaseModelResponse


class DispatchSummary(BaseModel):
    id: UUID
    terminated: bool


class DispatchCreateResponse(BaseModelResponse):
    execution_id: UUID
    terminated: bool = False
    worker_response: dict[str, Any]


class DispatchListItem(BaseListItem):
    execution_id: UUID
    terminated: bool = False
    worker_response: dict[str, Any]


class DispatchListResponse(BaseListResponse[DispatchListItem]):
    pass
